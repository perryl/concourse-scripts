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


def open_file(morphology):
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
            get_strata(yaml_stream)
        elif yaml_stream['kind'] == 'stratum':
            # Stratum parsed; parse chunks
            get_chunks(yaml_stream)
        else:
            pass

def get_strata(system_file):
    ''' Iterates through a yaml stream and finds all the strata'''
    # Iterate through the strata section of the system file
    for item in system_file['strata']:
        morph_path = '/home/lauren/Baserock/definitions/%s' % item['morph']
        open_file(morph_path)

def set_url(upstream, repo):
    url = 'http://git.baserock.org/cgi-bin/cgit.cgi/%s/%s.git' % (
          upstream, repo)
    return url

def generate_resources(strata, chunks):
    file_out = 'ymlfiles/jobs-%s.yml' % strata['name']
    with open(file_out, 'a') as f:
        for key, value in chunks.iteritems():
            f.write("- name: %s\n  type: git\n  source:\n    uri: %s\n" \
                    "    branch: %s\n\n" % (
                    value['name'], value['repo'], value['branch']))

def generate_jobs(strata, chunks):
    path = '%s/ymlfiles/' % os.getcwd()
    if not os.path.isdir(path):
        os.mkdir(path)
    file_out = 'ymlfiles/jobs-%s.yml' % strata['name']
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

def get_chunks(strata_file):
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
        item['repo'] = set_url(upstream, repo)
        if not 'unpetrify-ref' in item.keys():
            item['unpetrify-ref'] = 'master'
        chunk_collection.append(chunk_data)
    generate_jobs(strata_file, chunk_collection)

# Could implement a Class for the above fns, then call this in the Class main()
system_file = open_file('/home/lauren/Baserock/definitions/systems/base-system-x86_64-generic.morph')
