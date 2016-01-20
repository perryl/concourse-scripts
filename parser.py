#!/usr/bin/python
#
# parser.py
# Takes in a given morph system and parses the stratum required. Then parses
# the stratum and determines all the associated chunks
# Ultimate goal: output the chunks as YAML resource files for Concourse
# Copyright (c) Codethink 2016 All Rights Reserved

# plan:
# 1) open file
# 2) ensure file is system
# 3) parse file (using ybd methods?)
# 4) open strata or error if doesn't exist
# 5) parse strata and determine chunks
# For now, let's make this a fairly straightforward functional code and worry
# about making it class based later


import argparse
import yaml
import os
import re
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
        Error.__init__(self, 'Could not load file: %' % self.morph_file)


class SystemsParser():

    def open_file(self, morphology):
        '''Takes a file, ensure it is a system file and then open it'''
        with open(morphology, 'r') as f:
            try:
                yaml_stream = yaml.safe_load(f)
            except:
                raise YamlLoadError(file_name)
            if not isinstance(yaml_stream, dict):
                raise InvalidFormatError(file_name)
        return yaml_stream

    def get_strata(self, system_file, morphology):
        ''' Iterates through a yaml stream and finds all the strata'''
        # Iterate through the strata section of the system file
        morph_dir = re.sub('/systems', '', os.path.dirname(morphology))
        return ['%s/%s' % (morph_dir, strata['morph']) for strata in system_file['strata']]

    def transform_prefix(self, repo):
        return 'baserock' if 'baserock' in repo else 'delta'

    def get_job_from_strata(self, strata):
        inputs = [{'name': x['name']} for x in strata['chunks']]
        aggregates = [{'get': x['name'], 'resource': x['name'], 'trigger': True} for x in strata['chunks']]
        config = {'inputs': inputs, 'platform': 'linux', 'image': 'docker:///perryl/perryl-concourse#latest', 'run': {'path': './ybd/ybd/py', 'args': ['definitions']}}
        task = {'aggregates': aggregates, 'config': config, 'privileged': True}
        job = {'name': strata['name'], 'public': True, 'plan': [task]}
        return job

    def get_resource_from_chunk(self, x):
        resource = {'name': x['name'], 'type': 'git', 'source': {'uri': 'http://git.baserock.org/git/%s/%s' % (self.transform_prefix(x['repo']), re.search(':(.*)', x['repo']).groups(1)[0]), 'branch': x.get('unpetrify-ref', 'master')}}
        return resource

    def main(self):
        strata_yamls = []
        parser = argparse.ArgumentParser(
                 description='Takes Baserock system morphology.')
        parser.add_argument('--system', type=str)
        args = parser.parse_args()
        system_name = os.path.splitext(os.path.basename(args.system))[0]
        yaml_stream = self.open_file(args.system)
        if yaml_stream['kind'] == 'system':
            # Progress to parsing strata
            strata_paths = self.get_strata(yaml_stream, args.system)
            strata_yamls = [self.open_file(x) for x in strata_paths]
            jobs = [self.get_job_from_strata(x) for x in strata_yamls]
            resources = [[self.get_resource_from_chunk(x) for x in y['chunks']] for y in strata_yamls]
        else:
            pass
        system = {'jobs': jobs, 'resources': [x for y in resources for x in y]}
        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s-test.yml' % (path, system_name)
        with open(file_out, 'w') as f:
            f.write(yaml.dump(system, default_flow_style=False))

if __name__ == "__main__":
    SystemsParser().main()
