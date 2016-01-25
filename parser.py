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


import sys
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


class SystemsParser():

    def load_yaml_file(self, yaml_file):
        '''Loads the YAML from a given morphology.'''
        with open(yaml_file, 'r') as f:
            try:
                y = yaml.safe_load(f)
            except:
                raise YamlLoadError(yaml_file)
            if not isinstance(y, dict):
                raise InvalidFormatError(yaml_file)
            return y

    def get_all_strata(self, definitions_root, system_morph):
        ''' Iterates through a system morphology and returns all the strata'''
        system_strata = {stratum['morph']: self.load_yaml_file(os.path.join(
                             definitions_root, stratum['morph']))
                         for stratum in system_morph['strata']}

        def get_depends(strata):
            depends = {d['morph']: self.load_yaml_file(os.path.join(
                           definitions_root, d['morph']))
                       for d in strata.get("build-depends", [])
                       if d['morph'] not in system_strata}

            for d in depends.values():
                get_depends(d)
            system_strata.update(depends)

        for strata in system_strata.values():
            get_depends(strata)
        return system_strata

    def transform_prefix(self, repo):
        return 'baserock' if 'baserock' in repo else 'delta'

    def split_iterable(self, iterable, chunk_size):
        for i in xrange(0, len(iterable), chunk_size):
            yield iterable[i:i+chunk_size]

    def get_job_from_strata(self, strata, system_name, morphology, arch):
        inputs = [{'name': x['name']} for x in strata['chunks']]
        inputs.append({'name': 'definitions'})
        inputs.append({'name': 'ybd'})
        inputs.append({'name': 'setupybd'})
        definitions = {'get': 'definitions', 'resource': 'definitions', 'trigger': True}
        ybd = {'get': 'ybd', 'resource': 'ybd', 'trigger': True}
        morph_dir = re.sub('/systems', '', os.path.dirname(morphology))
        setup_ybd_task = {'task': 'setupybd', 'file': 'ybd/ci/setup.yml', 'config': {'params': {'YBD_CACHE_SERVER': '{{ybd-cache-server}}', 'YBD_CACHE_PASSWORD' : '{{ybd-cache-password}}'}}}
        build_depends = [self.all_strata[x['morph']]['name']
                         for x in strata.get('build-depends', [])]
        if build_depends:
            definitions.update({'passed': build_depends})
        aggregates = [{'get': x['name'], 'resource': x['name'], 'trigger': True, 'params': {'submodules': 'none'}} for x in strata['chunks']]
        aggregates.append(definitions)
        aggregates.append(ybd)
        cores = multiprocessing.cpu_count()
        aggregates_split = [{'aggregate': i} for i in self.split_iterable(aggregates, cores)]
        config = {'inputs': inputs, 'platform': 'linux', 'image': 'docker:///benbrown/sandboxlib#latest', 'run': {'path': './setupybd/ybd/ybd.py', 'args': ['definitions/strata/%s.morph' % strata['name'], arch]}}
        task = {'config': config, 'privileged': True, 'task': 'build'}
        plan = aggregates_split + [setup_ybd_task, task]
        job = {'name': strata['name'], 'public': True, 'plan': plan}
        return job

    def get_resource_from_chunk(self, x):
        resource = {'name': x['name'], 'type': 'git', 'source': {'uri': 'http://git.baserock.org/git/%s/%s' % (self.transform_prefix(x['repo']), re.search(':(.*)', x['repo']).groups(1)[0]), 'branch': x.get('unpetrify-ref', 'master')}}
        return resource

    def get_system_job(self, system_name, strata, arch):
        passed_list = [stratum['name'] for stratum in strata]
        aggregates = [{'get': 'definitions', 'resource': 'definitions', 'trigger': True, 'passed': passed_list}, {'get': 'ybd', 'resource': 'ybd', 'trigger': True}]
        config = {'inputs': [{'name': 'ybd'}, {'name': 'definitions'}], 'platform': 'linux', 'image': 'docker:///perryl/perryl-concourse#latest', 'run': {'path': './ybd/ybd.py', 'args': ['definitions/systems/%s.morph' % system_name, arch]}}
        plan = {'aggregate': aggregates, 'privileged': True, 'config': config}
        job = {'name': system_name, 'public': True, 'plan': [plan]}
        return job

    def main(self):
        if len(sys.argv) != 2:
            print "usage: %s SYSTEM_MORPHOLOGY" % os.path.basename(sys.argv[0])
            sys.exit(1)
        system_file = sys.argv[1]
        definitions_root = os.path.dirname(os.path.dirname(system_file))

        morphology = self.load_yaml_file(system_file)
        system_name = morphology['name']
        if morphology['kind'] == 'system':
            arch = morphology['arch']
            # Progress to parsing strata
            self.all_strata = self.get_all_strata(definitions_root, morphology)
            jobs = [self.get_job_from_strata(x, system_name, system_file, arch)
                    for x in self.all_strata.itervalues()]
            jobs.append(self.get_system_job(
                system_name, self.all_strata.itervalues(), arch))
            resources_by_strata = [[self.get_resource_from_chunk(x)
                                    for x in y['chunks']]
                                   for y in self.all_strata.itervalues()]
            resources = [x for y in resources_by_strata for x in y]
            resources.append({'name': 'definitions', 'type': 'git', 'source': {'uri': 'git://git.baserock.org/baserock/baserock/definitions.git', 'branch': 'master'}})
            resources.append({'name': 'ybd', 'type': 'git', 'source': {'uri': 'http://github.com/locallycompact/ybd', 'branch': 'master'}})
        if morphology['kind'] == 'stratum':
            arch = ''
            jobs = [self.get_job_from_strata(morphology, system_name, system_file, arch)]
            resources = [self.get_resource_from_chunk(x) for x in morphology['chunks']]
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
            stream = yaml.dump(system, default_flow_style=False)
            f.write(stream.replace("'{{ybd-cache-password}}'", "{{ybd-cache-password}}")
                          .replace("'{{ybd-cache-server}}'", "{{ybd-cache-server}}"))

if __name__ == "__main__":
    SystemsParser().main()
