# metagpsd

Python script that sends location updates from gpsd to a Kismet server.

Added in Kismet 2022-01-R3, data sources may use the metagps option. This script is intended to be used alongside a Kismet remote capture tool with a source using this new metagps option.

Special thanks to [@ckoval7](https://github.com/ckoval7/) and his work on [kisStatic2Mobile](https://github.com/ckoval7/kisStatic2Mobile) for the inspiration!

## Requirements

- websockets
- gpsd-py3

## Installing

### Install using Pipenv

    git clone https://github.com/hobobandy/python-kismet-metagpsd
    cd python-kismet-metagpsd && pipenv install
  
### Install using Pip

    git clone https://github.com/hobobandy/python-kismet-metagpsd
    cd python-kismet-metagpsd && pip install -r requirements.txt

## Usage

**NOTE:** Start the capture tool with metagps option before running metagpsd. Kismet needs to create the virtual gps before accepting metagpsd location updates.

    usage: metagpsd.py [-h] [--debug] --connect HOST_URI --metagps METAGPS --apikey APIKEY
    
    optional arguments:
      -h, --help          show this help message and exit
      --debug             enables debug logging (useful to log websockets requests)
    
    required arguments:
      --connect HOST_URI  address of kismet server (host:port)
      --metagps METAGPS   should match a data source's metagps option
      --apikey APIKEY     requires admin or WEBGPS role
