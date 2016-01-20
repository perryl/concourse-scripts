#!/usr/bin/python
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
                raise YamlLoadError(morphology)
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

    def get_job_from_strata(self, strata, system_name, morphology):
        inputs = [{'name': x['name']} for x in strata['chunks']]
        inputs.append({'name': 'definitions'})
        inputs.append({'name': 'ybd'})
        definitions = {'get': 'definitions', 'resource': 'definitions', 'trigger': True}
        ybd = {'get': 'ybd', 'resource': 'ybd', 'trigger': True}
        morph_dir = re.sub('/systems', '', os.path.dirname(morphology))
        build_depends = [self.open_file('%s/%s' % (morph_dir, x['morph']))['name'] for x in strata.get('build-depends', [])]
        if build_depends:
            definitions.update({'passed': build_depends})
        aggregates = [{'get': x['name'], 'resource': x['name'], 'trigger': True} for x in strata['chunks']]
        aggregates.append(definitions)
        aggregates.append(ybd)
        config = {'inputs': inputs, 'platform': 'linux', 'image': 'docker:///perryl/perryl-concourse#latest', 'run': {'path': './ybd/ybd/py', 'args': ['definitions/systems/%s.morph' % system_name]}}
        task = {'aggregate': aggregates, 'config': config, 'privileged': True}
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
            morph_dir = re.sub('/systems', '', os.path.dirname(args.system))
            build_depends_paths = ['%s/%s' % (morph_dir, a['morph']) for b in [x.get('build-depends',[]) for x in strata_yamls] for a in b]
            strata_paths = list(set(strata_paths) | set(build_depends_paths))
            strata_yamls = [self.open_file(x) for x in strata_paths]
            jobs = [self.get_job_from_strata(x, system_name, args.system) for x in strata_yamls]
            resources_by_strata = [[self.get_resource_from_chunk(x) for x in y['chunks']] for y in strata_yamls]
            resources = [x for y in resources_by_strata for x in y]
            resources.append({'name': 'definitions', 'type': 'git', 'source': {'uri': 'git://git.baserock.org/baserock/baserock/definitions.git', 'branch': 'master'}})
            resources.append({'name': 'ybd', 'type': 'git', 'source': {'uri': 'http://github.com/locallycompact/ybd', 'branch': 'master'}})
        else:
            pass
        system = {'jobs': jobs, 'resources': resources}
        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s.yml' % (path, system_name)
        with open(file_out, 'w') as f:
            f.write(yaml.dump(system, default_flow_style=False))

if __name__ == "__main__":
    SystemsParser().main()
