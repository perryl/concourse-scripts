#!/bin/sh

# This file, when ran, calls the parser python script to generate concourse
# pipelines; one for each stratum in the system specified in parser.py. The
# script will then set up each pipeline separately.

./parser.py
#vagrant init concourse/lite
#vagrant up

CWD=$PWD
cd $CWD/ymlfiles/
for file in '*.yml'; do
    fly set-pipeline -p $file -c $file
    fly unpause-pipeline -p $file
done
