#
# Copyright 2018-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError

from .debug import debug


class ConfigParseError(Exception):
    """
    Raised if a fatal error was encountered while the \
        configuration file was parsed.
    """
    pass


class ConfigurationError(Exception):
    """
    Raised if one or more settings in the configuration \
     file is missing or invalid.
    """

    def __init__(self, missing):
        assert isinstance(missing, list)
        self.missing = missing

    def get_missing_settings(self):
        return self.missing


class ConfigDef():
    """

    """

    config_def = [
        {
            'id': 'name',
            'key': 'name',
            'required': True,
            'default': None
        },
        {
            'id': 'model_identifier',
            'key': 'model_identifier',
            'required': True,
            'default': None
        },
        {
            'id': 'description',
            'key': 'description',
            'required': False,
            'default': None
        },
        {
            'id': 'author_name',
            'key': 'author,name',
            'required': True,
            'default': None
        },
        {
            'id': 'framework_name',
            'key': 'framework,name',
            'required': True,
            'default': None
        },
        {
            'id': 'framework_version',
            'key': 'framework,version',
            'required': True,
            'default': None
        },
        {
            'id': 'runtime_name',
            'key': 'framework,runtimes,name',
            'required': True,
            'default': None
        },
        {
            'id': 'runtime_version',
            'key': 'framework,runtimes,version',
            'required': True,
            'default': None
        },
        {
            'id': 'local_data_dir',
            'key': 'train,data_source,training_data_local,path',
            'required': False,
            'default': 'sample_training_data/'
        },
        {
            'id': 'training_bucket',
            'key': 'train,data_source,training_data,bucket',
            'required': True,
            'default': None
        },
        {
            'id': 'results_bucket',
            'key': 'train,model_training_results,trained_model,bucket',
            'required': True,
            'default': None
        },
        {
            'id': 'model_bucket',
            'key': 'train,model_source,initial_model,bucket',
            'required': False,
            'default': None
        },
        {
            'id': 'model_key_prefix',
            'key': 'train,model_source,initial_model,path',
            'required': False,
            'default': None
        },
        {
            'id': 'docker_model_asset_directory',
            'key': 'train,model_training_results,trained_model_local,path',
            'required': False,
            'default': '../assets/'
        },
        {
            'id': 'model_building_code_dir',
            'key': 'train,model_source,initial_model_local,path',
            'required': True,
            'default': None
        },
        {
            'id': 'training_run_execution_command',
            'key': 'train,execution,command',
            'required': True,
            'default': None
        },
        {
            'id': 'training_run_compute_configuration_name',
            'key': 'train,execution,compute_configuration,name',
            'required': True,
            'default': None
        },
        {
            'id': 'training_data_key_prefix',
            'key': 'train,data_source,training_data,path',
            'required': False,
            'default': ''
        }
    ]

    @staticmethod
    def get_def():
        """
        """
        required_keys = []
        optional_keys = []
        for entry in ConfigDef.config_def:
            if entry['required']:
                required_keys.append({
                                      'id': entry['id'],
                                      'key': entry['key']})
            else:
                optional_keys.append({
                                      'id': entry['id'],
                                      'key': entry['key'],
                                      'default': entry['default']})
        definitions = {
                        'required_keys': required_keys,
                        'optional_keys': optional_keys}
        return definitions


class YAMLReader():
    """
    Utility class that loads and validates a YAML formatted
    configuration file.
    """

    def __init__(self, config_file_name):
        # verify that name is an existing file
        if os.path.isfile(config_file_name):
            self.config_file = config_file_name
        else:
            raise FileNotFoundError('File {} was not found.'
                                    .format(config_file_name))

    def read(self):
        """
        Load configuration file in YAML format
        :returns: dict containing configuration values
        :rtype: dict
        :raises ConfigurationError: one or more configuration settings \
            is missing or invalid
        :raises ConfigParseError: the configuration file is not valid
        :raises FileNotFoundError: the configuration file was not found
        """

        debug('read()')

        resolved_config = {}
        try:
            yaml = YAML(typ='safe')
            yaml.default_flow_style = False
            # load and parse config file
            with open(self.config_file, 'r') as stream:
                config = yaml.load(stream)

            debug('Loaded input yaml "{}" into class {}:'
                  .format(config, type(config)))

            # if the configuration file ws not loaded into a dictionary
            # is it invalid; discard the input, which will trigger the
            # appropriate error
            if config is None or not isinstance(config, dict):
                config = {}

            def locate(root, path):
                for e in path.split(','):
                    if root.get(e) is not None:
                        root = root[e]
                    else:
                        return None
                return str(root)

            # determine whether all required configuration settings
            # were defined
            definitions = ConfigDef.get_def()
            missing_settings = []
            for entry in definitions['required_keys']:
                if locate(config, entry['key']) is not None:
                    resolved_config[entry['id']] = locate(config, entry['key'])
                else:
                    missing_settings.append(
                        {'key': entry['id'],
                         'yaml_path': entry['key'].replace(',', '.')})

            # additional processing required to obtain cos_endpoint_url
            if resolved_config.get('training_bucket') is not None:
                data_store_id = \
                    config['train']['data_source']['training_data'] \
                    .get('data_store')
                if data_store_id is None:
                    missing_settings.append(
                        {'key': 'cos_endpoint_url',
                         'yaml_path':
                            'train.data_source.training_data.data_store'})
                else:
                    # lookup data store
                    data_stores = config.get('data_stores', [])
                    found = False
                    for data_store in data_stores:
                        if data_store.get('name') != data_store_id:
                            continue
                        found = True
                        if data_store.get('connection') is None or \
                           data_store['connection'].get('endpoint') is None:
                            missing_settings.append(
                                {'key': 'cos_endpoint_url',
                                 'yaml_path':
                                    'data_stores.{}.connection.endpoint'
                                    .format(data_store_id)})
                            break
                        else:
                            resolved_config['cos_endpoint_url'] = \
                                        data_store['connection'] \
                                        .get('endpoint')
                            break
                    if not found:
                        missing_settings.append(
                            {'key': 'cos_endpoint_url',
                             'yaml_path': 'data_stores.{}'
                                          .format(data_store_id)})

            for p in config.get('process', []):
                if (p.get('name') or '').strip().lower() != 'training_process':
                    continue
                resolved_config['trained_model_path'] = \
                    (p.get('params')or {}).get('trained_model_path')
                resolved_config['local_download_directory'] = \
                    (p.get('params')or {}).get('staging_dir')
                break

            if resolved_config.get('trained_model_path') is None:
                missing_settings.append(
                    {'key': 'trained_model_path',
                     'yaml_path':
                        'process.training_process.params.trained_model_path'})
            if resolved_config.get('local_download_directory') is None:
                missing_settings.append(
                    {'key': 'local_download_directory',
                     'yaml_path':
                        'process.training_process.params.staging_dir'})

            if len(missing_settings) > 0:
                # at least one required configuration setting is missing
                raise ConfigurationError(missing_settings)

            # process optional configuration settings
            for entry in definitions['optional_keys']:
                if locate(config, entry['key']) is not None:
                    resolved_config[entry['id']] = locate(config, entry['key'])
                else:
                    resolved_config[entry['id']] = entry['default']

        except FileNotFoundError:
            # only triggered if the file was deleted after
            # the reader instance was created
            raise
        except DuplicateKeyError as dke:
            # http://yaml.readthedocs.io/en/latest/api.html#duplicate-keys
            raise ConfigParseError(dke)
        except ConfigurationError:
            raise
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise ConfigParseError(ex)

        # derive additional configuration settings

        # Model building code archive name
        resolved_config['model_code_archive'] = '{}-model-building-code.zip'. \
            format(resolved_config['model_identifier'])

        # WML training run name
        resolved_config['training_run_name'] = \
            'train-{}'.format(resolved_config['model_identifier'])

        # WML training run description
        resolved_config['training_run_description'] = \
            'Train {} '.format(resolved_config['name'])

        # Defines how frequently (in seconds) the utility will inspect the
        # WML training run status
        resolved_config['training_progress_monitoring_interval'] = 15

        return resolved_config
