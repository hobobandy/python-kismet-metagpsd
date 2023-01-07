__version__ = "2022.1"
__copyright__ = "2022, hobobandy"
__license__ = "MIT"
__author__ = "hobobandy"
__email__ = "hobobandy@gmail.com"
__version_int__ = "202201"


import argparse
import asyncio
import gpsd
import json
import logging
from logging.handlers import RotatingFileHandler
import signal
import threading
import websockets


class MetaGPSD:
    def __init__(self, host_uri, name, apikey):
        self.endpoint_uri = f"ws://{host_uri}/gps/meta/{name}/update.ws?KISMET={apikey}"
        self.exit_event = threading.Event()  # Event used for clean exit
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        logging.warning(f"Received {signal.Signals(signum).name}")
        self.stop()
    
    def stop(self):
        logging.info("Stopping")
        self.exit_event.set()
    
    async def run(self):
        # Initialize gpsd connection
        logging.info("Connecting to gpsd")
        gpsd.connect()
        await self.main(self.endpoint_uri)
    
    async def run_forever(self):
        while not self.exit_event.is_set():
            try:
                await self.run()
            except websockets.ConnectionClosed:
                logging.warning("Connection to kismet closed")
                continue

    async def main(self, endpoint_uri):
        try:
            logging.info("Connecting to kismet")
            async with websockets.connect(endpoint_uri) as websocket:
                logging.info("Sending location updates")
                while websocket and not self.exit_event.is_set():
                    # Poll gpsd for current location
                    gpsd_location = gpsd.get_current()
                    
                    # Prepare dict to be serialized to a JSON
                    kismet_location = { 'lat': gpsd_location.lat,
                                        'lon': gpsd_location.lon }
                    
                    if gpsd_location.mode == 3:
                        # alt 	Optional, GPS altitude in meters
                        kismet_location['alt'] = gpsd_location.alt
                    
                    if gpsd_location.hspeed <= 0:
                        # spd 	Optional, GPS speed in kilometers per hour
                        kismet_location['spd'] = gpsd_location.hspeed*(3600/1000)
                                
                    # Serialize the dict to a JSON string and send it!
                    await websocket.send(json.dumps(kismet_location))
                    await websocket.recv()
                                    
                    # Send 1 location update per second
                    await asyncio.sleep(1)
        except ConnectionRefusedError:
            logging.error("Failed to connect; check kismet is running, or host URI is valid. (host:port)")
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 404:
                logging.error("Kismet failed to find meta GPS name; check name matches the data source's metagps option.")
            elif e.status_code == 401:
                logging.error("Kismet rejected API key; check key is valid, and has admin or WEBGPS role.")
            else:
                logging.exception(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', dest="debug", action='store_true', help="enables debug logging (useful to log websockets requests)")
    # Simple hack to show "optional" arguments as required
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument("--connect", dest="host_uri", required=True, help="address of kismet server (host:port)")
    required_args.add_argument("--metagps", dest="metagps", required=True, help="should match a data source's metagps option")
    required_args.add_argument("--apikey", dest="apikey", required=True, help="requires admin or WEBGPS role")
    
    args = parser.parse_args()
    
    logging_handlers = list()
    
    if args.debug:
        logging_level = logging.DEBUG
        fh = RotatingFileHandler('metagpsd.log',
                             maxBytes=500000,  # 100kb
                             backupCount=1,
                             encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        logging_handlers.append(fh)
    else:
        logging_level = logging.INFO
    
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    logging_handlers.append(ch)
    
    logging.basicConfig(level=logging.DEBUG,
                        handlers=logging_handlers,
                        format='%(asctime)s %(name)-8s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    
    m = MetaGPSD(host_uri=args.host_uri, name=args.metagps, apikey=args.apikey)
    asyncio.run(m.run_forever())