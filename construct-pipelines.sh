#!/bin/sh
#
# Copyright (C) 2016  Codethink Limited
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =*= License: GPL-2 =*=

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
    yes | fly set-pipeline -p $file -c $file -l ../credentials.yml
done
