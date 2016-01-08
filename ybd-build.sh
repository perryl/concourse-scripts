#!/bin/sh

pip install pyyaml sandboxlib jsonschema bottle cherrypy requests

sudo mkdir -p /src

sudo ./ybd/ybd.py build-essential x86_64
sudo ./ybd/ybd.py base-system x86_64
