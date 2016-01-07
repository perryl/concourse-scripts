#!/bin/sh

sudo touch file
ls -l file
sudo mkdir -p /src

sudo ./ybd/ybd.py definitions/system/build-system-x86_64.morph x86_64
