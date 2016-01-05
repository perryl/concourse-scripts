#!/bin/sh

`sudo apt-get update && apt-get install python build-essential gawk git m4`

`wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py`
`pip install pyyaml sandboxlib jsonschema bottle cherrypy`
