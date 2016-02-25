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

    def create_get_dict(self, resource, additional_keyvals={}):
        return dict({'get': resource, 'attempts': 2}, **additional_keyvals)
    
    def get_ybd_task(self, inputs, ybd_args):
        sh_args = ['-c', 'echo "kbas-url: $YBD_CACHE_SERVER" >> ybd/ybd.conf; '
                   'echo "kbas-password: $YBD_CACHE_PASSWORD" >> ybd/ybd.conf; '
                   'echo "gits: $(pwd)" >> ybd/ybd.conf; '
                   './ybd/ybd.py %s' % ybd_args]
        return {'task': 'build', 'privileged': True, 'config':{
                    'platform': 'linux', 'image': 'docker_image',
                    'inputs': inputs, 'params': {
                        'YBD_CACHE_SERVER': '{{ybd-cache-server}}',
                        'YBD_CACHE_PASSWORD': '{{ybd-cache-password}}'
                    }, 'run': {'path': 'sh', 'args': sh_args}}}

    def main(self):
        '''
        Generate a pipeline for the given strata and tests
        '''
        parser = argparse.ArgumentParser(
            description='Generate a pipeline for a strata and tests')
        parser.add_argument('strata', type=str,
                            help='The location of the strata in the \
                                  definitions repo')
        parser.add_argument('definitionsurl', type=str,
                            help='The URL of the definitions under \
                                  test')
        parser.add_argument('branch', type=str,
                            help='The branch of definitions to be \
                                  tested', default='master')
        parser.add_argument('tests', type=str,
                            help='The URL of the tests to be run on \
                                  the built system', default=None)
        parser.add_argument('test-branch', type=str,
                            help='The branch of the tests to be run \
                                  on the built system',
                            default='master')
        args = parser.parse_args()

        resources = []
        resources.append({'name': 'definitions', 'type': 'git',
                          'check_every': '15m', 'source': {
                              'uri': args.definitionsurl,
                              'branch': args.branch}})
        resources.append({'name': 'ybd', 'type': 'git', 'source':
                          {'uri': 'https://github.com/devcurmudgeon/ybd',
                           'branch': '16.08'}})

        jobs = []
        definitions_res = self.create_get_dict("definitions")
        ybd_res = self.create_get_dict("ybd")
        aggregates = []
        aggregates.append(definitions_res)
        aggregates.append(ybd_res)
        strata_task = self.get_ybd_task(args.strata, "x86_64")
        strata_plan = aggregates + [strata_task]
        system_task = self.get_ybd_task("systems/genivi-demo-platform-x86_64-generic.morph", "x86_64")
        system_plan = aggregates + [system_task]
        # TODO: check how arch and system name should be defined
        
        jobs.append({'name': args.strata, 'public': True,
                     'plan': strata_plan})
        jobs.append({'name': 'gdp-x86_64-generic', 'public': True,
                     'plan': system_plan})
        system = {'jobs': jobs, 'resources': resources}
        with open("file_out.yaml", 'w') as f:
            stream = yaml.dump(system, default_flow_style=False)
            f.write(stream.replace("'{{ybd-cache-password}}'",
                                   "{{ybd-cache-password}}")
                          .replace("'{{ybd-cache-server}}'",
                                   "{{ybd-cache-server}}"))
        print "Done"

if __name__ == "__main__":
    StrataGenerator().main()
