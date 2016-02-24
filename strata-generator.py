#!/usr/bin/env python2
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

import string
import argparse
import yaml
import os
import re
import multiprocessing
from collections import OrderedDict


class Error(Exception):
    pass

class InvalidFormatError(Error):

    def __init__(self, morph_file):
        self.morph_file = morph_file
        Error.__init__(self, 'Morphology is not a dict: %s' % self.morph_file)

class YamlLoadError(Error):

    def __init__(self, morph_file):
        self.morph_file = morph_file
        Error.__init__(self, 'Could not load file: %s' % self.morph_file)

class StrataGenerator():

    def main(self):
        '''
        Generate a pipeline for the given strata and tests
        '''
        parser = argparse.ArgumentParser(
            description='Generate a pipeline for a strata and tests')
        parser.add_argument('--strata', type=str,
                            help='The location of the strata in the \
                                  definitions repo')
        parser.add_argument('--definitions-url', type=str,
                            help='The URL of the definitions under \
                                  test')
        parser.add_argument('--branch', type=str,
                            help='The branch of definitions to be \
                                  tested', default='master')
        parser.add_argument('--tests', type=str,
                            help='The URL of the tests to be run on \
                                  the built system', default=None)
        args = parser.parse_args()

        
