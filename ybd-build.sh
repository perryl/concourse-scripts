#!/bin/sh

whoami

`sudo mkdir -p /src`

sudo ./ybd/ybd.py definitions/system/build-system-x86_64.morph x86_64
