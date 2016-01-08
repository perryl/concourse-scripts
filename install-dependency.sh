#!/bin/sh

sudo apt-get update && sudo apt-get install -y \
  python build-essential gawk git m4 wget sudo python-dev python-pip \
  libyaml-dev libxml2-dev libxslt-dev

sudo wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

sudo pip install pyyaml sandboxlib jsonschema bottle cherrypy requests
