#!/bin/bash

mkdir -p /src

cd ybd

python setup.py install

./ybd/ybd.py definitions/system/build-system-x86_64.morph x86_64
