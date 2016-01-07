#!/bin/sh

sudo ./scripts/install-dependency.sh
sudo mkdir -p /src

echo "BUILDING build-essential\n"
sudo ./ybd/ybd.py build-essential x86_64
echo "\nBUILDING base-system\n"
sudo ./ybd/ybd.py definitions/systems/base-system-x86_64-generic.morph x86_64
