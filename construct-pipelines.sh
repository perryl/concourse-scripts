#!/bin/sh

# This file, when ran, calls the parser python script to generate concourse
# pipelines; one for each stratum in the system specified in parser.py. The
# script will then set up each pipeline separately.

./parser.py

CWD=$PWD
cd $CWD/ymlfiles/
for file in '*.yml'; do
    yes | fly set-pipeline -p $file -c $file
done