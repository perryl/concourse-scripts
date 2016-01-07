#!/bin/sh

DIR=$PWD
cd /
sudo mkdir -p src
cd $DIR

sudo ./ybd/ybd.py definitions/system/build-system-x86_64.morph x86_64
