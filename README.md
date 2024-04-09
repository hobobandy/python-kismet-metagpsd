# metagpsd

Python script that sends location updates from gpsd to a Kismet server.

Added in Kismet 2022-01-R3, data sources may use the metagps option. This script is intended to be used alongside a Kismet remote capture tool with a source using this new metagps option. [Kismet MetaGPS Reference](https://kismetwireless.net/docs/readme/remotecap/remotecap/#remote-capture-and-gps)

Special thanks to [@ckoval7](https://github.com/ckoval7/) and his work on [kisStatic2Mobile](https://github.com/ckoval7/kisStatic2Mobile) for the inspiration!

## Installing

### Install using Pip

```
git clone https://github.com/hobobandy/python-kismet-metagpsd
cd python-kismet-metagpsd
pip install -r requirements.txt
```

## Usage

**NOTE:** Start the capture tool with metagps option before running metagpsd. Kismet needs to create the virtual gps before accepting metagpsd location updates.

**WARNING:** Prior to [8 April 2024](https://github.com/kismetwireless/kismet/commit/cc482240904d5b6ba7c04fc993f5e2ebc24e6a86), Kismet's average location will include 0,0 locations that will skew the average. Start metagpsd as soon as possible after the capture tool.

### Example

* key1 should have admin or datasource role
* key2 should have admin or WEBGPS (custom) role

```
$ sudo kismet_cap_linux_wifi --connect <ip>:2501 --apikey <key1> --source wlan1:name=remote0,metagps=remote0 --daemonize
$ python metagpsd.py --connect <ip>:2501 --metagps remote0 --apikey <key2>
```

### Help

```
usage: metagpsd.py [-h] --connect HOST_URI --metagps METAGPS --apikey APIKEY [--ssl] [--debug]

options:
  -h, --help          show this help message and exit
  --ssl               use secure connection
  --debug             enable debug output

required arguments:
  --connect HOST_URI  address of kismet server (host:port)
  --metagps METAGPS   should match a data source's metagps option
  --apikey APIKEY     requires admin or WEBGPS (custom) role
```
