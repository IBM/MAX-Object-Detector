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

import requests


class MainHandler:

    def __init__(self, resource_id, iam_access_token, ins_obj, ins_handle):

        assert iam_access_token is not None, \
            'Parameter access token cannot be None'
        assert resource_id is not None, 'Parameter resource_id cannot be None'
        assert ins_obj is not None, \
            'Parameter ins_obj (ServiceHandler instance) cannot be None.'
        assert ins_handle is not None, \
            'Parameter ins_handle (InstanceHandler instance) cannot be None'

        self.ins_obj = ins_obj
        self.ins_handle = ins_handle
        self.resource_id = resource_id
        self.iam_access_token = iam_access_token

    def wml_block(self):  # noqa
        """
        Handles Watson Machine Learning related operations.
        1. Get all WML available instances.
        2. Create new WML instance and key if desired.
        3. Use existing instance and key if chosen.
        4. Use existing instance and create a new key, if chosen.
        :return: WML environment variables such as apikey,
                 url and instance id.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        print('-------------------------------------------------------------'
              '------------------------')
        print('Choose an existing Watson Machine Learning service instance '
              'or create a new instance: ')
        print('-------------------------------------------------------------'
              '------------------------')
        # Call function to retrieve available instances and their
        # respective ids
        existing_instances, instance_option, existing_guids = \
            self.ins_handle.available_instance('wml', self.resource_id)
        # Prompt new instance name for creation.
        # If user did not provide any name, prompt again.
        # If the entered name already exists, prompt again.
        if existing_instances[int(instance_option) - 1] == \
                'Create New Instance':
            wml_location, wml_plan, wml_resource_plan_id = \
                self.ins_obj.get_wml_deployment_details()
            print('-----------------------------------------------------------'
                  '-------------------')
            print('Creating Watson Machine Learning service instance')
            print('-----------------------------------------------------------'
                  '-------------------')
            while True:
                wml_name = input("[PROMPT] Enter an instance name: ").strip()
                if wml_name == '':
                    continue
                elif wml_name in existing_instances:
                    print("[MESSAGE] A service instance with this name already"
                          " exists. Pick a different name.")
                    continue
                else:
                    break
            # create a new Watson Machine Learning instance using the provided
            #  name, selected location,
            # resource and plan id. Instance id is retrieved on successful
            # completion of creation.
            wml_instance_guid = self.ins_obj.service_create(
                 wml_name, wml_location, self.resource_id,
                 wml_resource_plan_id)
            print('----------------------------------------------------'
                  '--------------------------')
            print('Creating Watson Machine Learning service credentials ')
            print('----------------------------------------------------'
                  '--------------------------')
            while True:
                wml_key_name = input("[PROMPT] Enter a "
                                     "service credentials name: ").strip()
                if wml_key_name == '':
                    continue
                else:
                    break
            # WML key creation using user and credential retrieval
            wml_apikey, instance_id, url = \
                self.ins_obj.wml_key_create(wml_key_name, wml_instance_guid)
            return wml_apikey, instance_id, url
        else:
            print("[MESSAGE] Using existing service instance '{}'. "
                  .format(existing_instances[int(instance_option) - 1]))

            message = """
*----------------------------------------------------------------------------*
|                                                                            |
| Service credentials are used to access IBM Cloud services, such as         |
| Watson Machine Learning.                                                   |
|                                                                            |
*----------------------------------------------------------------------------*
            """
            print(message)
            print('----------------------------------------------------'
                  '----------------------------------')
            print('Choose existing Watson Machine Learning service '
                  'credentials or create new credentials:')
            print('----------------------------------------------------'
                  '----------------------------------')
            # Get existing keys and their guid.
            existing_keys, key_option, existing_key_guid = \
                self.ins_handle.wml_key_check(
                    existing_guids[int(instance_option) - 1])
            if existing_keys[int(key_option) - 1] == 'Create New Key':
                print('-------------------------------------------------'
                      '-----------------------------')
                print('Creating Watson Machine Learning service credentials')
                print('-------------------------------------------------'
                      '-----------------------------')
                while True:
                    wml_key = input("[PROMPT] Enter a "
                                    "service credentials name: ").strip()
                    if wml_key == '':
                        continue
                    if wml_key in existing_keys:
                        print("[MESSAGE] Service credentials name already "
                              "taken. Please enter a different name.")
                        continue
                    else:
                        break
                # WML Key creation and credential retrieval
                wml_apikey, instance_id, url = \
                    self.ins_obj.wml_key_create(
                        wml_key, existing_guids[int(instance_option) - 1])
                return wml_apikey, instance_id, url
            else:
                print("[MESSAGE] Using existing Watson Machine Learning "
                      "service credentials '{}'. "
                      .format(existing_keys[int(key_option) - 1]))
                # Retrieve details from the existing key details.
                wml_key_details = requests.get(
                    'https://resource-controller.cloud.ibm.com/v2/'
                    'resource_keys/' + existing_key_guid[
                        int(key_option) - 1], headers=headers)
                if wml_key_details.status_code == 200:
                    wml_key_details = wml_key_details.json()
                    try:
                        # Extract necessary environment variables from the
                        # credentials.
                        wml_apikey = \
                            wml_key_details['credentials']['apikey']
                        instance_id = \
                            wml_key_details['credentials']['instance_id']
                        url = \
                            wml_key_details['credentials']['url']
                        return wml_apikey, instance_id, url
                    except KeyError:
                        print(''''  ERROR !!!!    ''')
                        raise KeyError("Choose appropriate Cloud Object "
                                       "Storage guid corresponding to the"
                                       " credentials name")

    def cos_block(self):  # noqa
        """
        Handles Cloud Object Storage related operations.
        1. Get all COS available instances.
        2. Create new instance and Key if desired.
        3. Use existing instance and key if chosen.
        4. Use existing instance and create a new key, if chosen.
        :return: COS environment variables such as resource_instance_id,
        apikey, access_key and secret_access_key.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        print('---------------------------------------------------'
              '-------------------------------')
        print('Choose an existing Cloud Object Storage service instance '
              'or create a new instance:')
        print('---------------------------------------------------'
              '-------------------------------')
        # Call function to retrieve available instances and their
        # respective ids
        existing_instances, instance_option, existing_guids = \
            self.ins_handle.available_instance('cos', self.resource_id)
        # Prompt new instance name for creation.
        # If user did not provide any name, prompt again.
        # If the entered name already exists, prompt again.
        if existing_instances[int(instance_option) - 1] == \
                'Create New Instance':
            cos_plan, cos_resource_plan_id = \
                self.ins_obj.get_cos_deployment_details()
            print('------------------------------------------'
                  '------------------------------------')
            print('Creating Cloud Object Storage service instance  ')
            print('-------------------------------------------'
                  '-----------------------------------')
            while True:
                cos_name = input("[PROMPT] Enter Cloud Object Storage "
                                 "service instance name: ").strip()
                if cos_name == '':
                    continue
                elif cos_name in existing_instances:
                    print("[MESSAGE] A Cloud Object Storage service instance "
                          "with this name already exists. "
                          "Please enter a different name.")
                    continue
                else:
                    break
            # create a new Watson Machine Learning instance using the
            # provided name, selected location,
            # resource and plan id. Instance id is retrieved on
            # successful completion of creation.
            cos_instance_guid = self.ins_obj.service_create(
                cos_name, "global", self.resource_id, cos_resource_plan_id)
            print('----------------------------------------------'
                  '--------------------------------')
            print('Creating Cloud Object Storage service credentials')
            print('----------------------------------------------'
                  '--------------------------------')
            while True:
                cos_key_name = input("[PROMPT] Enter a Cloud Object Storage"
                                     " service credentials name: ").strip()
                if cos_key_name != '':
                    break
            # COS Key creation and environment variable retrieval
            resource_instance_id, apikey, access_key, secret_access_key = \
                self.ins_obj.cos_key_create(cos_key_name, cos_instance_guid)
            return resource_instance_id, apikey, access_key, secret_access_key
        else:
            print("[MESSAGE] Using existing Cloud Object Storage service "
                  "instance '{}'. "
                  .format(existing_instances[int(instance_option) - 1]))
            print('  ')
            print('----------------------------------------------------'
                  '-------------------------------')
            print('Choose existing Cloud Object Storage service '
                  'credentials or create new credentials:')
            print('----------------------------------------------------'
                  '-------------------------------')
            # Get existing keys and their guid.
            existing_keys, key_option, existing_key_guid = \
                self.ins_handle.cos_key_check(
                    existing_guids[int(instance_option) - 1])
            if existing_keys[int(key_option) - 1] == 'Create New Key':
                print('------------------------------------------------'
                      '------------------------------')
                print('Creating Cloud Object Storage service credentials')
                print('------------------------------------------------'
                      '------------------------------')
                while True:
                    cos_key = input("[PROMPT] Enter a Cloud Object Storage"
                                    " service credentials name: ").strip()
                    if cos_key == '' or cos_key in existing_keys:
                        print("[MESSAGE] Service credentials with this "
                              "name already exist. "
                              "Please enter a different name.")
                        continue
                    else:
                        break
                resource_instance_id, apikey, access_key, secret_access_key = \
                    self.ins_obj.cos_key_create(
                        cos_key, existing_guids[int(instance_option) - 1])
                return resource_instance_id, apikey, \
                    access_key, secret_access_key
            else:
                print("[MESSAGE] Using existing Cloud Object Storage "
                      "service credentials '{}'. "
                      .format(existing_keys[int(key_option) - 1]))
                # Retrieve details from the existing key details.
                obj_key_details = requests.get(
                    'https://resource-controller.cloud.ibm.com'
                    '/v2/resource_keys/' +
                    existing_key_guid[int(key_option) - 1], headers=headers)
                if obj_key_details.status_code == 200:
                    obj_key_details = obj_key_details.json()
                    try:
                        # Extract necessary environment variables
                        # from the credentials.
                        resource_instance_id = obj_key_details['credentials'][
                            'resource_instance_id']
                        apikey = \
                            obj_key_details['credentials']['apikey']
                        access_key = \
                            obj_key_details['credentials']['cos_hmac_keys'][
                                'access_key_id']
                        secret_access_key = \
                            obj_key_details['credentials']['cos_hmac_keys'][
                                'secret_access_key']
                        return resource_instance_id, apikey, \
                            access_key, secret_access_key
                    except KeyError:
                        print(''''  ERROR !!!!    ''')
                        raise KeyError("Choose appropriate Cloud Object "
                                       "Storage guid corresponding to "
                                       "the service credentials name")
