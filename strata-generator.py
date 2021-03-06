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


docker_image = "docker:///benbrown/sandboxlib#latest"


class StrataGenerator():

    def create_get_dict(self, resource, **kwargs):
        # TODO: For a demo, we will be using a vagrant box which does
        # not support attempts. For production, switch this round
        # return dict({'get': resource, 'attempts': 3}, **kwargs)
        return dict({'get': resource}, **kwargs)

    def get_ybd_task(self, inputs, ybd_args):
        sh_args = ['-c', 'echo "kbas-url: $YBD_CACHE_SERVER" >> ybd/ybd.conf; '
                   'echo "kbas-password: $YBD_CACHE_PASSWORD" >> ybd/ybd.conf;'
                   ' echo "gits: $(pwd)" >> ybd/ybd.conf; '
                   './ybd/ybd.py %s' % ybd_args]
        return {'task': 'build', 'privileged': True, 'config': {
                'platform': 'linux', 'image': docker_image,
                'inputs': inputs, 'params': {
                    'YBD_CACHE_SERVER': '{{ybd-cache-server}}',
                    'YBD_CACHE_PASSWORD': '{{ybd-cache-password}}'},
                'run': {'path': 'sh', 'args': sh_args}}}

    def get_test_task(self):
        test_aggregates = []
        test_aggregates.append(
            self.make_aggregate_dependencies("gdp-x86_64-generic"))

        sh_args = ['-c', 'echo "Testing is Not Yet Implemented"',
                   'exit 0']
        test_task = {'task': 'pretend-to-test', 'config': {
            'platform': 'linux', 'image': docker_image},
            'run': {'path': 'sh', 'args': sh_args}}
        test_plan = test_aggregates + [test_task]
        return test_plan

    def make_aggregate_dependencies(self, dependency):
        '''
        Returns a dict of definitions that is required to have passed
        the given dependency
        '''

        dependent_aggregates = self.create_get_dict("definitions", **{
            'trigger': True, 'passed': [dependency]})
        return dependent_aggregates

    def main(self):
        '''
        Generate a pipeline for the given strata and tests
        '''
        parser = argparse.ArgumentParser(
            description='Generate a pipeline for a strata and tests')
        parser.add_argument('--strata', type=str, required=True,
                            help='The strata name')
        parser.add_argument('--definitions-url', type=str, required=True,
                            help='The URL of the definitions under test')
        parser.add_argument('--branch', type=str, default='master',
                            help='The branch of definitions to be tested')
        parser.add_argument('--tests', type=str, default=None,
                            help='The URL of the tests to be run on the '
                            'built system')
        parser.add_argument('--test-branch', type=str, default='master',
                            help='The branch of the tests to be run on the '
                            'built system')
        args = parser.parse_args()

        resources = []
        resources.append({'name': 'definitions', 'type': 'git',
                          'check_every': '15m', 'source': {
                              'uri': args.definitions_url,
                              'branch': args.branch}})
        resources.append({'name': 'ybd', 'type': 'git', 'source':
                          {'uri': 'https://github.com/devcurmudgeon/ybd',
                           'branch': '16.08'}})

        jobs = []
        definitions_res = self.create_get_dict("definitions")
        ybd_res = self.create_get_dict("ybd")

        # There are three tasks required for the dev workflow: strata,
        # system and test. Here we define the plans for them
        strata_aggregates = []
        strata_aggregates.append(definitions_res)
        strata_aggregates.append(ybd_res)

        system_aggregates = []
        system_aggregates.append(self.make_aggregate_dependencies(args.strata))
        system_aggregates.append(ybd_res)

        inputs = [{'name': 'definitions'}, {'name': 'ybd'}]
        strata_task = self.get_ybd_task(inputs,
                                        "definitions/strata/%s.morph %s" % (
                                            args.strata, "x86_64"))
        strata_plan = strata_aggregates + [strata_task]
        system_task = self.get_ybd_task(inputs, "definitions/systems/"
                                        "genivi-demo-platform-x86_64-generic"
                                        ".morph %s" % "x86_64")
        system_plan = system_aggregates + [system_task]
        # TODO: check how arch and system name should be defined

        jobs.append({'name': args.strata, 'public': True,
                     'plan': strata_plan})
        jobs.append({'name': 'gdp-x86_64-generic', 'public': True,
                     'plan': system_plan})
        if args.tests is not None:
            test_job = self.get_test_task()
            jobs.append({'name': 'test', 'public': True,
                        'plan': test_job})

        system = {'jobs': jobs, 'resources': resources}

        Dumper = yaml.SafeDumper
        Dumper.ignore_aliases = lambda self, data: True

        with open("file_out.yaml", 'w') as f:
            stream = yaml.dump(system, default_flow_style=False, Dumper=Dumper)
            f.write(stream.replace("'{{ybd-cache-password}}'",
                                   "{{ybd-cache-password}}")
                          .replace("'{{ybd-cache-server}}'",
                                   "{{ybd-cache-server}}"))
        print "Done"

if __name__ == "__main__":
    StrataGenerator().main()
