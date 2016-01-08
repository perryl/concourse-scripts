#!/bin/sh

sudo ./scripts/install-dependency.sh
sudo mkdir -p /src

sudo ./ybd/ybd.py build-essential x86_64
sudo ./ybd/ybd.py base-system x86_64
