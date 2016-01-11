#!/bin/sh

sudo mkdir -p /src

sudo ./ybd/ybd.py build-essential x86_64
sudo ./ybd/ybd.py definitions/systems/base-system-x86_64-generic.morph x86_64
