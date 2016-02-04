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


aliases = {
  'baserock:': 'git://git.baserock.org/baserock/',
  'freedesktop:': 'git://anongit.freedesktop.org/',
  'github:': 'git://github.com/',
  'gnome:': 'git://git.gnome.org/',
  'upstream:': 'git://git.baserock.org/delta/'
}

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

    def get_repo_url(self, repo):
        for alias, url in aliases.items():
            repo = repo.replace(alias, url)
        if repo.endswith('.git'):
            repo = repo[:-4]
        return repo


    def get_repo_name(self, repo):
        ''' Convert URIs to strings that only contain digits, letters, _ and %.

        NOTE: this naming scheme is based on what lorry uses

        '''
        valid_chars = string.digits + string.ascii_letters + '%_'
        transl = lambda x: x if x in valid_chars else '_'
        return ''.join([transl(x) for x in self.get_repo_url(repo)])

    def load_yaml_from_file(self, morph_file):
        '''Loads the YAML from a given morphology.'''
        with open(morph_file, 'r') as f:
            try:
                y = yaml.safe_load(f)
            except:
                raise YamlLoadError(morph_file)
            if not isinstance(y, dict):
                raise InvalidFormatError(morph_file)
            return y

    def get_strata(self, system_file):
        ''' Iterates through a system morphology and returns all the strata'''
        return ['%s/%s' % (
                self.morph_dir,
                strata['morph']) for strata in system_file['strata']]

    def transform_prefix(self, repo):
        return 'baserock' if 'baserock' in repo else 'delta'

    def split_iterable(self, iterable, chunk_size):
        for i in xrange(0, len(iterable), chunk_size):
            yield iterable[i:i+chunk_size]

    def get_job_from_strata(self, strata, morphology, arch, resources):
        repos = set(x['repo'] for x in strata['chunks'])
        inputs = [{'name': resources[repo]['name'],
                   'path': self.get_repo_name(repo)}
                  for repo in repos]
        inputs.append({'name': 'definitions'})
        inputs.append({'name': 'ybd'})
        inputs.append({'name': 'setupybd'})
        definitions = {'get': 'definitions', 'resource': 'definitions',
                       'trigger': True}
        ybd = {'get': 'ybd', 'resource': 'ybd'}
        morph_dir = re.sub('/systems', '', os.path.dirname(morphology))
        setup_ybd_task = {'task': 'setupybd', 'file': 'ybd/ci/setup.yml',
                          'config': {'params': {
                              'YBD_CACHE_SERVER': '{{ybd-cache-server}}',
                              'YBD_CACHE_PASSWORD': '{{ybd-cache-password}}'}}}
        build_depends = [self.load_yaml_from_file('%s/%s' % (
                         morph_dir, x['morph']))['name'] for x in strata.get(
                         'build-depends', [])]
        if build_depends:
            definitions.update({'passed': build_depends})
        aggregates = [{'get': resources[repo]['name'],
                       'params': {'submodules': 'none'}}
                      for repo in repos]
        aggregates.append(definitions)
        aggregates.append(ybd)
        cores = multiprocessing.cpu_count()
        aggregates_split = [{'aggregate': i} for i in self.split_iterable(
            aggregates, cores)]
        sh_args = ['-c', 'echo "gits: $(pwd)" >> setupybd/ybd/ybd.conf; '
                   './setupybd/ybd/ybd.py definitions/strata/%s.morph %s' %
                   (strata['name'], arch)]
        config = {'inputs': inputs, 'platform': 'linux', 'image':
                  'docker:///benbrown/sandboxlib#latest',
                  'run': {'path': 'sh', 'args': sh_args}}
        task = {'config': config, 'privileged': True, 'task': 'build'}
        plan = aggregates_split + [setup_ybd_task, task]
        job = {'name': strata['name'], 'public': True, 'plan': plan}
        return job

    def get_strata_resources(self, all_strata):
        all_chunks = (c for stratum in all_strata
                      for c in stratum['chunks'])
        resources = {}
        for chunk in all_chunks:
            name = os.path.basename(chunk['repo'].rsplit(":", 1)[1])
            resources[chunk['repo']] = {
                'name': name, 'type': 'git', 'check_every': '15m',
                'source': {
                    'uri': self.get_repo_url(chunk['repo']),
                    'branch': chunk.get('unpetrify-ref', 'master')}}
        return resources

    def get_strata_paths(self, strata_path):
        yaml = self.load_yaml_from_file(strata_path)
        build_depends_paths = ['%s/%s' % (
                               self.morph_dir,
                               a['morph']) for a in yaml.get(
                                   'build-depends', [])]
        bdds = [a for b in [self.get_strata_paths(x)
                for x in build_depends_paths] for a in b]
        x = list(set([strata_path]) | set(build_depends_paths) | set(bdds))
        return x

    def get_system_job(self, system_name, strata_paths, arch):
        passed_list = [os.path.splitext(
                       os.path.basename(x))[0] for x in strata_paths]
        aggregates = [{'get': 'definitions', 'resource': 'definitions',
                       'trigger': True, 'passed': passed_list},
                      {'get': 'ybd', 'resource': 'ybd'}]
        config = {'inputs': [{'name': 'ybd'}, {'name': 'definitions'}],
                  'platform': 'linux',
                  'image': 'docker:///benbrown/sandboxlib#latest',
                  'run': {'path': './ybd/ybd.py', 'args': [
                      'definitions/systems/%s.morph' % system_name, arch]}}
        plan = {'aggregate': aggregates, 'privileged': True, 'config': config}
        job = {'name': system_name, 'public': True, 'plan': [plan]}
        return job

    def main(self):
        strata_yamls = []
        parser = argparse.ArgumentParser(
            description='Takes Baserock system morphology.')
        parser.add_argument('--system', type=str)
        args = parser.parse_args()
        yaml_stream = self.load_yaml_from_file(args.system)
        system_name = yaml_stream['name']
        self.morph_dir = re.sub('/systems', '', os.path.dirname(args.system))
        if yaml_stream['kind'] == 'system':
            arch = yaml_stream['arch']
            # Progress to parsing strata
            strata_paths = self.get_strata(yaml_stream)
            strata_paths = list(set([a for b in [self.get_strata_paths(x)
                                for x in strata_paths] for a in b]))
            strata_yamls = [self.load_yaml_from_file(x) for x in strata_paths]
        if yaml_stream['kind'] == 'stratum':
            arch = ''
            strata_yamls = [yaml_stream]

        resources_by_name = self.get_strata_resources(strata_yamls)
        resources = resources_by_name.values()
        resources.append({'name': 'definitions', 'type': 'git',
            'check_every': '15m', 'source': {'uri':
                'git://git.baserock.org/baserock/baserock/definitions.git',
                'branch': 'master'}})
        resources.append({'name': 'ybd', 'type': 'git', 'source':
                          {'uri': 'https://github.com/locallycompact/ybd',
                           'branch': 'benbrown/revert-for-green'}})
        jobs = [self.get_job_from_strata(
                    x, args.system, arch, resources_by_name)
                for x in strata_yamls]
        if yaml_stream['kind'] == "stratum":
            jobs.append(self.get_system_job(system_name, strata_paths, arch))

        system = {'jobs': jobs, 'resources': resources}
        path = '%s/%s' % (os.getcwd(), system_name)
        if not os.path.isdir(path):
            os.mkdir(path)
        file_out = '%s/%s.yml' % (path, system_name)
        with open(file_out, 'w') as f:
            stream = yaml.dump(system, default_flow_style=False)
            f.write(stream.replace("'{{ybd-cache-password}}'",
                                   "{{ybd-cache-password}}")
                          .replace("'{{ybd-cache-server}}'",
                                   "{{ybd-cache-server}}"))

if __name__ == "__main__":
    SystemsParser().main()
