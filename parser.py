#!/usr/bin/python
#
# parser.py
# Takes in a given morph system and parses the stratum required. Then parses the
# stratum and determines all the associated chunks
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

# GOALS
# Morning 1: Parse basic system and get a list of all chunks saved to dict
#            Chunks should be associated explicitly with the relevant strata
#            Order of strata build should be determined


import yaml
import os
import re
from collections import OrderedDict


def open_file(morphology):
    '''Takes a file, ensure it is a system file and then open it'''
    with open(morphology, 'r') as f:
        try:
            yaml_stream = yaml.safe_load(f)
        except:
            #TODO: proper error class
            #raise YamlLoadError(file_name)
            print "lolno"
            exit()
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
    url = 'http://git.baserock.org/cgi-bin/cgit.cgi/%s/%s.git' % (upstream, repo)
    return url

def generate_resources(chunk):
    file_out = 'ymlfiles/%s.yml' % chunk['name']
    with open(file_out, 'w') as f:
        f.write("resources:\n- name: %s\n  type: git\n  source:\n    uri: %s" \
                "\n    branch: %s" % (
                chunk['name'], chunk['repo'], chunk['branch']))

def get_chunks(strata_file):
    chunk_collection = {}
    for item in strata_file['chunks']:
        if 'baserock:' in item['repo']:
            repo = re.sub('baserock:', '', item['repo'])
            upstream = 'baserock'
        else:
            repo = re.sub('upstream:', '', item['repo'])
            upstream = 'delta'
        chunk_collection['name'] = item['name']
        chunk_collection['repo'] = set_url(upstream, repo)
        if 'unpetrify-ref' in item.keys():
            chunk_collection['branch'] = item['unpetrify-ref']
        else:
            chunk_collection['branch'] = 'master'
        generate_resources(chunk_collection)

# Could implement a Class for the above fns, then call this in the Class main()
system_file = open_file('/home/lauren/Baserock/definitions/systems/base-system-x86_64-generic.morph')
