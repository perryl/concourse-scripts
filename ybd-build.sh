#!/bin/sh

sudo ./scripts/install-dependency.sh
sudo mkdir -p /src

echo "BUILDING stage1-binutils\n"
sudo ./ybd/ybd.py stage1-binutils x86_64
echo "BUILDING build-essential\n"
sudo ./ybd/ybd.py build-essential x86_64
echo "\n\n\n"
cat /root/ybd/artifacts/stage1-gcc.842188c5f6d594e1bbaf358262fe8988e7494aec19e84c410b425f87ba2ab0e2.build-log
echo "\n\n\n"
echo "\nBUILDING base-system\n"
sudo ./ybd/ybd.py definitions/systems/base-system-x86_64-generic.morph x86_64
