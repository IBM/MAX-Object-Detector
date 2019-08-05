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

from .debug import debug

import json
import re
from watson_machine_learning_client import WatsonMachineLearningAPIClient
from watson_machine_learning_client.wml_client_error import ApiRequestFailure


class WMLWrapperError(Exception):
    pass


class WMLWrapper:
    """Basic wrapper class for common WML tasks
    """

    @staticmethod
    def parse_WML_ApiRequestFailure(arf):
        """
        Utility function parses ApiRequestFailure, which is
        raised by WatsonMachineLearningAPIClient

        :param arf: ApiRequestFailure
        :type arf: ApiRequestFailure
        :return: parsed exception
        :rtype: dict
        """
        if arf is None or not isinstance(arf, ApiRequestFailure):
            return None

        debug('WML ApiRequestFailure Exception: {}'.format(arf))

        if not arf.error_msg:
            return None

        # holds the components of an ApiRequestFailure
        parsed_arf = {
            'raw_message_text': [],
            'status_code': None,   # HTTP status code
            'json_body': None,     # a dict, if JSON message
            'error_message': None  # raw error message
        }
        try:
            for line in arf.error_msg.split('\n'):
                parsed_arf['raw_message_text'].append(line)
                m = re.match(r'Status code: (\d\d\d), body: (.*)$',
                             line)
                if m:
                    parsed_arf['status_code'] = int(m.group(1))
                    try:
                        # try to parse the error message if
                        # it is JSON encoded
                        parsed_arf['json_body'] = \
                            json.loads(m.group(2))
                        if parsed_arf['json_body'].get('errors') and\
                           isinstance(parsed_arf['json_body']['errors'], list)\
                                and\
                           len(parsed_arf['json_body']['errors']) > 0:
                            parsed_arf['error_message'] = \
                                parsed_arf['json_body']['errors'][0]\
                                .get('message')
                        else:
                            parsed_arf['error_message'] = \
                                '\n'.join(parsed_arf['raw_message_text'])
                    except Exception:
                        # not JSON; use message body
                        parsed_arf['error_message'] = m.group(2)
            return parsed_arf
        except Exception as ex:
            print('Error trying to parse WML ApiRequestFailure: {}'
                  .format(arf))
            debug(' Message: {}'.format(arf.error_msg))
            debug(' Exception:', ex)

    def __init__(self,
                 url,
                 api_key,
                 instance_id):
        """
        Initializer

        """

        try:
            self.client = WatsonMachineLearningAPIClient({
                            'url': url,
                            'apikey': api_key,
                            'instance_id': instance_id
                            })
            self.client.service_instance.get_details()
        except ApiRequestFailure as arf:
            debug('Exception: {}'.format(arf))
            p = WMLWrapper.parse_WML_ApiRequestFailure(arf)
            if p:
                msg = p['error_message']
            else:
                msg = arf.error_msg
            raise WMLWrapperError(
                    'Error. Cannot connect to WML service: {}'
                    .format(msg))
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise WMLWrapperError(ex)

    def get_client(self):
        return self.client

    def start_training(self,
                       model_building_archive,
                       model_definition_metadata,
                       training_configuration_metadata):
        """
        Start WML training
        :param model_building_archive: path to zipped model_definition
        :type model_building_archive: str

        :param model_definition_metadata: model definition metadata
        :type model_definition_metadata: dict

        :param training_configuration_metadata: training definition metadata
        :type training_configuration_metadata: dict

        :returns: training run guid
        :rtype: str

        :raises WMLWrapperError: an error occurred
        """

        assert model_building_archive is not None, \
            'Parameter model_building_archive cannot be None'
        assert model_definition_metadata is not None, \
            'Parameter model_definition_metadata cannot be None'
        assert training_configuration_metadata is not None, \
            'Parameter training_configuration_metadata cannot be None'

        debug('parm training_configuration_metadata:',
              training_configuration_metadata)
        debug('parm model_definition_metadata:', model_definition_metadata)

        try:

            # Store training definition into Watson Machine Learning
            # repository on IBM Cloud.
            definition_details = \
                self.client.repository.store_definition(
                                        model_building_archive,
                                        model_definition_metadata)

            debug('store_definition details:', definition_details)

            # Get uid of stored definition
            definition_uid = \
                self.client.repository.get_definition_uid(definition_details)

            debug('get_definition_uid:', definition_uid)

            # Train model
            training_run_details = \
                self.client.training.run(definition_uid,
                                         training_configuration_metadata)

            debug('run details: ', training_run_details)

            # Get uid of training run
            run_uid = self.client.training.get_run_uid(training_run_details)

            debug('run uid: {}'.format(run_uid))

            return run_uid
        except Exception as ex:
            raise(WMLWrapperError(ex))

    def is_known_training_id(self,
                             training_guid):
        """
        Determines whether training_guid is known to the
        associated Watson Machine Learning service instance

        :param training_guid: training id
        :type training_guid: str

        :returns: True if this is a valid training id
        :rtype: bool

        :raises WMLWrapperError: an error occurred
        """

        assert training_guid is not None, \
            'Parameter training_guid cannot be None'

        try:
            # fetch status for this training id
            self.client.training.get_status(training_guid)
            return True
        except ApiRequestFailure as arf:
            debug('Exception type: {}'.format(type(arf)))
            debug('Exception: {}'.format(arf))
            p = WMLWrapper.parse_WML_ApiRequestFailure(arf)
            if p and p.get('status_code') == 404:
                return False
            raise WMLWrapperError(arf)

    def get_training_status(self,
                            training_guid,
                            ignore_server_error=False):
        """ Get status of a training run.

            :param training_guid: Existing WML training run guid
            :type training_guid: str

            :param ignore_server_error: if set, None is returned
            if an HTTP 5xx status code was returned by the service
            :type ignore_server_error: bool

            :returns: training run status, or None
            :rtype: dict

            :raises WMLWrapperError: an error occurred
        """

        assert training_guid is not None, \
            'Parameter training_guid cannot be None'

        status = None
        try:
            status = self.client.training.get_status(training_guid)
        except ApiRequestFailure as arf:
            debug('Exception type: {}'.format(type(arf)))
            debug('Exception: {}'.format(arf))
            p = WMLWrapper.parse_WML_ApiRequestFailure(arf)
            if p and p.get('status_code') >= 500 and ignore_server_error:
                return None
            raise WMLWrapperError(arf)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise WMLWrapperError(ex)

        debug('Training status: ', status)

        # Example status
        # {
        #   "state": "completed",
        #   "finished_at": "2019-04-15T22:24:58.648Z",
        #   "submitted_at": "2019-04-15T22:21:15.907Z",
        #   "running_at": "2019-04-15T22:21:52.940Z",
        #   "message": "training-Ax5PvBRWg: ",
        #   "metrics": [],
        #   "current_at": "2019-04-15T22:25:25.500Z"
        # }

        return status

    def get_training_results_references(self,
                                        training_guid,
                                        ignore_server_error=False):
        """ Get status of a training run
            :param training_guid: Existing WML training run guid
            :type training_guid: str

            :param ignore_server_error: if set, None is returned
            if an HTTP 5xx status code was returned by the service
            :type ignore_server_error: bool

            :returns: training run status
            :rtype: dict

            :raises WMLWrapperError: an error occurred
        """

        assert training_guid is not None, \
            'Parameter training_guid cannot be None'

        details = None
        try:
            # fetch details for this training run
            details = self.client.training.get_details(training_guid)
            debug('Training run details:', details)
        except ApiRequestFailure as arf:
            debug('Exception type: {}'.format(type(arf)))
            debug('Exception: {}'.format(arf))
            p = WMLWrapper.parse_WML_ApiRequestFailure(arf)
            if p and p.get('status_code') >= 500 and ignore_server_error:
                return None
            raise WMLWrapperError(arf)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise WMLWrapperError(ex)

        # extract results bucket name and model location from the response
        if ((details.get('entity', None) is not None) and
            (details['entity']
                .get('training_results_reference', None) is not None) and
            (details['entity']['training_results_reference']
                .get('location', None) is not None)):
            return(
                details['entity']['training_results_reference']['location'])
        # the response did not contain the expected results
        return {}

    def cancel_training(self,
                        training_guid,
                        not_found_ok=True):
        """
        Attempt to cancel the training run identified by training_guid

        :param training_guid: training run to be canceled
        :type training_guid: str
        :param not_found_ok: no error if the training id is invalid,
        defaults to True
        :type not_found_ok: bool, optional
        """

        assert training_guid is not None, \
            'Parameter training_guid cannot be None'

        try:
            self.client.training.cancel(training_guid)
        except ApiRequestFailure as arf:
            debug('Exception type: {}'.format(type(arf)))
            debug('Exception: {}'.format(arf))
            p = WMLWrapper.parse_WML_ApiRequestFailure(arf)
            if p and p.get('status_code') == 404 and not_found_ok:
                return
            raise WMLWrapperError(arf)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise WMLWrapperError(ex)
        return
