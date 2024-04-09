import argparse
import asyncio
import json
import signal
import sys
import threading
import websockets

from gpsdclient import GPSDClient
from loguru import logger


class MetaGPSD:
    def __init__(self, host_uri, name, apikey, use_ssl=False):
        self.endpoint_uri = f"{'wss' if use_ssl else 'ws'}://{host_uri}/gps/meta/{name}/update.ws?KISMET={apikey}"
        self.exit_event = threading.Event()  # Event used for clean exit
        self.gpsdclient = None
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        logger.warning(f"Received {signal.Signals(signum).name}")
        self.exit()
    
    def exit(self):
        self.exit_event.set()
    
    async def run_forever(self):
        while not self.exit_event.is_set():
            try:
                await self.main()
            except websockets.ConnectionClosed:
                logger.warning("Connection to Kismet closed")
                continue
        logger.info("Exiting")
    
    async def main(self):
        try:
            logger.info("Connecting to GPSd")
            with GPSDClient() as self.gpsdclient:
                logger.info("Connecting to Kismet")
                logger.debug(f"URI: {self.endpoint_uri}")
                async with websockets.connect(self.endpoint_uri) as websocket:
                    logger.info("Sending location updates")
                    while websocket and not self.exit_event.is_set():
                        # Poll gpsd for current location
                        for result in self.gpsdclient.dict_stream(filter=["TPV"]):
                            gpsd_location = result
                            break
                        
                        # Prepare dict to be serialized to a JSON
                        kismet_location = { "lat": gpsd_location["lat"],
                                            "lon": gpsd_location["lon"]}
                        
                        if gpsd_location["mode"] == 3:
                            # alt 	Optional, GPS altitude in meters
                            kismet_location["alt"] = gpsd_location["alt"]
                        
                        if gpsd_location["speed"] <= 0:
                            # spd 	Optional, GPS speed in kilometers per hour
                            kismet_location["spd"] = gpsd_location["speed"]*(3600/1000)
                        
                        logger.debug(kismet_location)
                                    
                        # Serialize the dict to a JSON string and send it!
                        await websocket.send(json.dumps(kismet_location))
                        await websocket.recv()
                                        
                        # Send 1 location update per second
                        await asyncio.sleep(1)
        except ConnectionRefusedError:
            logger.error("Failed to connect; check Kismet is running, or host URI is valid. (host:port)")
            self.exit()
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 404:
                logger.error("Kismet failed to find meta GPS name; check name matches the data source's metagps option.")
            elif e.status_code == 401:
                logger.error("Kismet rejected API key; check key is valid, and has admin or WEBGPS role.")
            else:
                logger.exception(e)
            self.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Simple hack to show "optional" arguments as required
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument("--connect", dest="host_uri", required=True, help="address of kismet server (host:port)")
    required_args.add_argument("--metagps", dest="metagps", required=True, help="should match a data source's metagps option")
    required_args.add_argument("--apikey", dest="apikey", required=True, help="requires admin or WEBGPS (custom) role")
    # optional
    parser.add_argument("--ssl", dest="use_ssl", action='store_true', help="use secure connection")
    parser.add_argument("--debug", dest="debug", action='store_true', help="enable debug output")
    
    args = parser.parse_args()

    if not args.debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")
    
    m = MetaGPSD(host_uri=args.host_uri, name=args.metagps, apikey=args.apikey, use_ssl=args.use_ssl)
    asyncio.run(m.run_forever())
