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
            if yaml_stream['kind'] == 'system':
                # Progress to parsing strata
                self.get_strata(yaml_stream, system_name)
            elif yaml_stream['kind'] == 'stratum':
                # Stratum parsed; parse chunks
                self.get_chunks(yaml_stream, system_name)
            else:
                pass

    def get_strata(self, system_file, system_name):
        ''' Iterates through a yaml stream and finds all the strata'''
        # Iterate through the strata section of the system file
        for item in system_file['strata']:
            morph_path = '/home/lauren/Baserock/definitions/%s' % item['morph']
            self.open_file(morph_path, system_name)

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
            item['repo'] = self.set_url(upstream, repo)
            if not 'unpetrify-ref' in item.keys():
                item['unpetrify-ref'] = 'master'
            chunk_collection.append(chunk_data)
        self.generate_jobs(strata_file, chunk_collection, system_name)

    def generate_jobs(self, strata, chunks, system_name):
        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s.yml' % (path, strata['name'])
        previous_item = None
        with open(file_out, 'w') as f:
            f.write("jobs:\n\n")
            for key, value in strata.iteritems():
                if key == 'chunks':
                    f.write("- name: %s\n  public: true\n" % strata['name'])
                    f.write("  plan:\n  - aggregate:\n")
                    for chunk in value:
                        f.write("    - get: %s\n      resource: %s\n" % (
                                chunk['name'], chunk['name']))
                        f.write("      trigger: true\n")
                    if previous_item is not None:
                        f.write("    passed: %s" % previous_item)
                    previous_item = strata['name']
                    f.write("    privileged: true\n    config:\n      inputs:\n")
                    for chunk in value:
                        f.write("      - {name: %s}\n" % chunk['name'])
                    f.write("      platform: linux\n      ")
                    f.write("image: docker:///perryl/perryl-concourse#latest\n")
                    f.write("      run:\n        path: ./ybd/ybd.py\n")
                    f.write("        args: [definitions/strata/%s.morph]\n\n" % (
                            strata['name']))
                    f.write("resources:\n")
                    for chunk in value:
                        f.write("- name: %s\n  type: git\n  source:\n    uri: %s" \
                                "\n    branch: %s\n\n" % (
                                chunk['name'], chunk['repo'],
                                chunk['unpetrify-ref']))
                else:
                    pass

    def main(self):
        parser = argparse.ArgumentParser(
                 description='Takes Baserock system morphology.')
        parser.add_argument('--system', type=str)
        args = parser.parse_args()
        system_name = os.path.splitext(os.path.basename(args.system))[0]
        self.open_file(args.system, system_name)

if __name__ == "__main__":
    SystemsParser().main()
