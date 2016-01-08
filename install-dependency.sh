#!/bin/sh

sudo wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

sudo pip install pyyaml sandboxlib jsonschema bottle cherrypy requests
