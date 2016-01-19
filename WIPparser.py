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

    def open_file(self, morphology, system_name):
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
        morph_path = []
        for item in system_file['strata']:
            morph_path.append('%s/%s' % (morph_dir, item['morph']))
        return morph_path

    def set_url(self, upstream, repo):
        url = 'http://git.baserock.org/cgi-bin/cgit.cgi/%s/%s.git' % (
              upstream, repo)
        return url

    def get_chunks(self, strata_file, system_name):
        chunk_collection = []
        chunk_data = {}
        for item in strata_file['chunks']:
            if 'baserock:' in item['repo']:
                repo = re.sub('baserock:', '', item['repo'])
                upstream = 'baserock'
            else:
                repo = re.sub('upstream:', '', item['repo'])
                upstream = 'delta'
            chunk_data['name'] = item['name']
            chunk_data['repo'] = self.set_url(upstream, repo)
            if not 'unpetrify-ref' in item.keys():
                chunk_data['unpetrify-ref'] = 'master'
            chunk_collection.append(chunk_data)
        return chunk_collection

    def generate_jobs(self, strata, chunks, system_name):
        jobs = {}
        resources = {}
        plan = {}
        config = {}
        run = {}
        aggregate = {}
        input = {}
        source = {}

        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s-test.yml' % (path, system_name)

        if not 'build-depends' in strata.keys():
            passed = ''
        else:
            passed = strata['build-depends']
        with open(file_out, 'a') as f:
            for key, value in strata.iteritems():
                if key == 'chunks':
                    jobs['name'] = strata['name']
                    jobs['public'] = 'True'
                    jobs['trigger'] = 'True'
                    jobs['passed'] = '[%s]' % passed
                    jobs['plan'] = plan
                    for chunk in value:
                        aggregate['get'] = chunk['name']
                    aggregate['resource'] = chunk['name']
                    aggregate['trigger'] = 'True'
                    aggregate['passed'] = '[%s]' % passed
                    plan['aggregate'] = aggregate
                    plan['task'] = strata['name']
                    plan['privileged'] = 'True'
                    plan['config'] = config
                    for chunk in value:
                        input['name'] = chunk['name']
                    config['input'] = input
                    config['platform'] = 'linux'
                    config['image'] = 'docker:///perryl/perryl-concourse#latest'
                    run['args'] = '[ definitions/strata/%s.morph ]' % strata['name']
                    run['path'] = './ybd/ybd.py'
                    config['run'] = run
                    for chunk in value:
                        source['branch'] = chunk['unpetrify-ref']
                        source['uri'] = chunk['repo']
                        resources['source'] = source
                        resources['name'] = chunk['name']
                        resources['type'] = 'git'
                else:
                    pass
        return jobs, resources


    def main(self):
        jobs = {}
        resources = {}
        parsed = False
        parser = argparse.ArgumentParser(
                 description='Takes Baserock system morphology.')
        parser.add_argument('--system', type=str)
        args = parser.parse_args()
        system_name = os.path.splitext(os.path.basename(args.system))[0]
        yaml_stream = self.open_file(args.system, system_name)
        if yaml_stream['kind'] == 'system':
            # Progress to parsing strata
            morph_path = self.get_strata(yaml_stream, args.system)
            for strata_path in morph_path:
                yaml_stream = self.open_file(strata_path, system_name)
                # Stratum parsed; parse chunks
                chunk_collection = self.get_chunks(yaml_stream, system_name)
                jobs, resources = self.generate_jobs(
                    yaml_stream, chunk_collection, system_name)
            parsed = True
        if yaml_stream['kind'] == 'stratum' and not parsed:
            # Stratum parsed; parse chunks
            chunk_collection = self.get_chunks(yaml_stream, system_name)
            jobs, resources = self.generate_jobs(
                yaml_stream, chunk_collection, system_name)
        else:
            pass
        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s-test.yml' % (path, system_name)
        with open(file_out, 'w') as f:
            f.write(yaml.dump(jobs, default_flow_style=False))
            f.write(yaml.dump(resources, default_flow_style=False))

if __name__ == "__main__":
    SystemsParser().main()
