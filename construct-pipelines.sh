#!/bin/sh

set -e

# This file, when ran, calls the parser python script to generate concourse
# pipelines; one for each stratum in the system specified in parser.py. The
# script will then set up each pipeline separately.

if [ "$#" != "1" ]
then
    echo "Invalid # arguments"
    echo "Usage: ./construct-pipelines.sh definitions/systems/build-system-x86_64.morph"
    exit 1
fi

build_system="$1"
system_name=$(basename "$build_system" ".morph")
./parser.py --system="$build_system"

CWD=$PWD
cd $CWD/$system_name/
for file in *.yml; do
    yes | fly set-pipeline -p $file -c $file
done
