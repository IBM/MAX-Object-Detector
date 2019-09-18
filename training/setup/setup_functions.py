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
import sys
import json


class InstanceHandler:

    def __init__(self, iam_access_token):
        assert iam_access_token is not None, \
            'Parameter access token cannot be None'
        self.iam_access_token = iam_access_token
        with open('setup/config.json') as config_file:
            self.data = json.load(config_file)

    def get_instance_details(self, response, which_resource,
                             inter_list, count):
        """
        Get details of the available instances.
        :param response: response from the request
        :param which_resource: `wml` or `cos`.
        :param inter_list: intermediate list holding details about
                           the resources.
        :param count: number of resources retrieved.
        :return: intermediate list and resources count.
        """
        for index, value in enumerate(response['resources'], start=1):
            # check instances under the specified resource
            for index_1, plan in \
                    enumerate(value['plan_history'], start=1):
                for key, values in \
                        enumerate(self.data[which_resource].items()):
                    if plan['resource_plan_id'] == values[1]:
                        count += 1
                        inter_list.append([count, value['name'],
                                           value['region_id'],
                                           values[0], value['guid']])
        return inter_list, count

    def available_instance(self, which_resource, resource_group_id): # noqa
        """
        This function retrieves available instances of
        specified service and prompts user to select the instance
        to be used for training.
        1. Available service resource plan ids of instances are
           checked against the standard service resource plan id
           values corresponding to the provided service and resource id.
        2. Displays the available resource plan ids of instances
           under the chosen service.
        3. Prompts user to enter the index of the displayed instances
           of their choice. User can also choose to create a new instance.
        4. If there is no available instance, user will be taken
           directly to instance creation step.
        :param which_resource: under which service, standard service
               resource plan id needs to be searched.
        :param resource_group_id: under which resource group, availability
                                  of instances need to be searched.
        :return: List of existing instances, guids and
                 selected option. Exit on error
        """
        if which_resource == 'wml':
            resource_id = self.data['resource-id']['wml']
        elif which_resource == 'cos':
            resource_id = self.data['resource-id']['cos']
        resource_param = {
            "resource_group_id": resource_group_id,
            "resource_id": resource_id
        }
        headers = {
            'Authorization': self.iam_access_token,
        }
        response = requests.get("https://resource-controller."
                                "cloud.ibm.com/v2/resource_instances",
                                headers=headers, params=resource_param)
        if response.status_code == 200:
            response = response.json()
            # list to append existing instances
            existing_instances = []
            # list to append existing guids
            existing_guids = []
            count = 0
            next_page_flag = 'N'
            inter_list = []
            inter_list, count = \
                self.get_instance_details(response,
                                          which_resource,
                                          inter_list,
                                          count)
            # retrieve instances available under
            if response['next_url'] is not None:
                next_page_flag = 'Y'
            while True:
                if next_page_flag == 'N':
                    break
                else:
                    response = requests.get("https://resource-controller."
                                            "cloud.ibm.com" +
                                            response['next_url'],
                                            headers=headers)
                    if response.status_code == 200:
                        response = response.json()
                        inter_list, count = \
                            self.get_instance_details(response,
                                                      which_resource,
                                                      inter_list,
                                                      count)
                        if response['next_url'] is None:
                            next_page_flag = 'N'
            inter_list.sort(key=lambda x: x[1].casefold())
            for list_index, list_val in enumerate(inter_list, start=1):
                print("{:2d}. Instance Name: {}   |  "
                      "Instance Location: {}  | "
                      "Instance Plan: {} ".
                      format(list_index, list_val[1], list_val[2],
                             list_val[3]))
                existing_instances.append(list_val[1])
                existing_guids.append(list_val[4])
            # Adding create new instance option.
            if len(existing_instances) > 0:
                print('{:2d}. {}'.format(int(count) + 1,
                                         '* Create New Instance *'))
                existing_instances.append('Create New Instance')
                existing_guids.append('Create New Guid')
            else:
                # Default instance create option when no instances are found
                print('{:2d}. {}'.format(1, 'Create New Instance'))
            # Prompt user to input choice and return lists and choice.
            if len(existing_instances) > 0 and \
                    existing_instances[0] != 'Create New Instance':
                while True:
                    instance_option = input("[PROMPT] Your selection:  ") \
                                      .strip()
                    if not instance_option.isdigit() or \
                       int(instance_option) < 1 or \
                       (int(instance_option) >= (len(existing_instances) + 1)):
                        print("[MESSAGE] Enter a number between 1 and "
                              "{}.".format(len(existing_instances)))
                        continue
                    else:
                        return existing_instances, instance_option, \
                               existing_guids
            else:
                return ['Create New Instance'], '1', ['Create New Guid']

        else:
            print("[DEBUG] Failing with status code:", response.status_code)
            print("[DEBUG] Reason for failure:", response.reason)
            sys.exit()

    def wml_key_details(self, available_keys, count,
                        inter_wml_list):
        """
        Get details of the WML keys matching guid of the instance.
        :param available_keys: response from the request
        :param count: count to track number of retrieved keys
                      under the selected instance.
        :param inter_wml_list: intermediate list holding details of
                               the key retrieved.
        :return: intermediate list and count
        """
        for index, key in enumerate(available_keys['resources'], start=1):
            count += 1
            inter_wml_list.append([count, key['name'], key['guid']])

        return inter_wml_list, count

    def wml_key_check(self, instance_guid): # noqa
        """
        This function:
        1. Retrieves list of keys under provided instance guid.
        2. Prompts user choice to choose from existing
           keys or create new key
        :param instance_guid: guid of instance under
               which presence of keys need to be searched.
        :return: list of existing keys, guid of keys and user
               choice. Exit when error occurs in key retrieval request.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        available_keys = requests.get("https://resource-controller.cloud."
                                      "ibm.com/v2/resource_instances/"
                                      + instance_guid +
                                      "/resource_keys",
                                      headers=headers)
        if available_keys.status_code == 200:
            available_keys = available_keys.json()
            # list for storing existing keys and list
            existing_keys = []
            existing_keys_guid = []
            inter_wml_list = []
            count = 0
            next_page_flag = 'N'
            inter_wml_list, count = \
                self.wml_key_details(available_keys,
                                     count,
                                     inter_wml_list)
            if available_keys['next_url'] is not None:
                next_page_flag = 'Y'
            while True:
                if next_page_flag == 'N':
                    break
                else:
                    available_keys = requests.get("https://resource-"
                                                  "controller.cloud.ibm"
                                                  ".com" +
                                                  available_keys['next_url'],
                                                  headers=headers)
                    if available_keys.status_code == 200:
                        available_keys = available_keys.json()
                        inter_wml_list, count = \
                            self.wml_key_details(available_keys,
                                                 count,
                                                 inter_wml_list)
                        if available_keys['next_url'] is None:
                            next_page_flag = 'N'

            inter_wml_list.sort(key=lambda x: x[1].casefold())
            for list_index, list_val in enumerate(inter_wml_list, start=1):
                print("{:2d}. Key Name: {} ".format(list_index, list_val[1]))
                existing_keys.append(list_val[1])
                existing_keys_guid.append(list_val[2])
            print('{:2d}. {}'.format(count + 1,
                                     '* Create New Service Credentials *'))
            existing_keys.append('Create New Key')
            if len(existing_keys) > 0:
                while True:
                    key_option = input("[PROMPT] Your selection:  ").strip()
                    if not key_option.isdigit() or \
                       int(key_option) < 1 or \
                       int(key_option) >= (len(existing_keys) + 1):
                        print("[MESSAGE] Enter a number between 1 and "
                              "{}.".format(len(existing_keys)))
                        continue
                    else:
                        return existing_keys, key_option, existing_keys_guid
            else:
                return ['Create New Key'], '1', []
        else:
            print('[DEBUG] key not present')
            print("[DEBUG] Failing with status code:",
                  available_keys.status_code)
            print("[DEBUG] Reason for failure:", available_keys.reason)
            sys.exit()

    def cos_key_details(self, available_keys,
                        inter_cos_list, count):
        """
        Get details of the COS keys matching guid of the instance.
        :param available_keys: response from the request
        :param inter_cos_list: intermediate list holding details of
                               the key retrieved.
        :param count: count to track number of retrieved keys
                      under the selected instance.
        :return: intermediate list and count
        """
        for index, k in enumerate(available_keys['resources'], start=1):
            count += 1
            inter_cos_list.append([count, k['name'], k['guid']])

        return inter_cos_list, count

    def cos_key_check(self, instance_guid): # noqa
        """
        This function:
        1. Retrieves list of keys under
           provided instance guid.
        2. Prompts user choice to choose from existing
           keys or create new key
        :param instance_guid: guid of instance under which
               presence of keys need to be searched.
        :return: list of existing keys, guid of keys and user
               choice. Exit when error occurs in key retrieval request.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        available_keys = requests.get("https://resource-controller."
                                      "cloud.ibm.com/v2/resource_instances/"
                                      + instance_guid +
                                      "/resource_keys",
                                      headers=headers)
        if available_keys.status_code == 200:
            available_keys = available_keys.json()
            # list for storing existing keys and list
            existing_keys = []
            existing_keys_guid = []
            inter_cos_list = []
            count = 0
            next_page_flag = 'N'
            inter_cos_list, count = \
                self.cos_key_details(available_keys,
                                     inter_cos_list, count)
            if available_keys['next_url'] is not None:
                next_page_flag = 'Y'
            while True:
                if next_page_flag == 'N':
                    break
                else:
                    available_keys = requests.get("https://resource-"
                                                  "controller.cloud."
                                                  "ibm.com" +
                                                  available_keys['next_url'],
                                                  headers=headers)
                    if available_keys.status_code == 200:
                        available_keys = available_keys.json()
                        inter_cos_list, count = \
                            self.cos_key_details(available_keys,
                                                 inter_cos_list, count)
                        if available_keys['next_url'] is None:
                            next_page_flag = 'N'
            inter_cos_list.sort(key=lambda x: x[1].casefold())
            for list_index, list_val in enumerate(inter_cos_list, start=1):
                print("{:2d}. Key Name: {} ".format(list_index, list_val[1]))
                existing_keys.append(list_val[1])
                existing_keys_guid.append(list_val[2])
            print('{:2d}. {}'.format(count + 1,
                                     '* Create New Service Credentials *'))
            existing_keys.append('Create New Key')
            # Prompt for user input
            if len(existing_keys) > 0:
                while True:
                    key_option = input("[PROMPT] Your selection:  ").strip()
                    if not key_option.isdigit() or \
                       int(key_option) < 1 or \
                       int(key_option) >= (len(existing_keys) + 1):
                        print("[MESSAGE] Enter a number between 1 and "
                              "{}.".format(len(existing_keys)))
                        continue
                    else:
                        return existing_keys, key_option, \
                               existing_keys_guid
            else:
                return ['Create New Key'], '1', []
        else:
            print('[DEBUG] key not present')
            print("[DEBUG] Failing with status code:",
                  available_keys.status_code)
            print("[DEBUG] Reason for failure:",
                  available_keys.reason)
            sys.exit()
