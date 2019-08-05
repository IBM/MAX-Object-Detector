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

import sys
import requests
import json


class ServiceHandler:
    """
    This class handles IBM Cloud services.

    1. Retrieve service instance information.
    2. Retrieve instance key information.
    3. Check for existing instance and key
    4. Retrieve resource ids
    """

    def __init__(self, iam_access_token):
        """

        :param iam_access_token: IBM cloud access token
        """
        assert iam_access_token is not None, \
            'Parameter access token cannot be None'
        self.iam_access_token = iam_access_token

    def get_resources_id(self):
        """
        Retrieve available resources. Prompt user
        choice if there are more than one resource.
        :return: resource id. Exit on error in resource id retrieval.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        response = requests.get('https://resource-controller.'
                                'cloud.ibm.com/v2/resource_groups',
                                headers=headers)
        if response.status_code == 200:
            response = response.json()
            # list to store resource values
            resources_list = []
            resources_name = []
            print('-----------------------------------------------'
                  '-------------------------')
            print('Available resource groups: ')
            print('-----------------------------------------------'
                  '-------------------------')
            for ind, value in enumerate(response['resources'], start=1):
                print("{:2d}. {}".format(ind, value['name']))
                resources_name.append(value['name'])
                resources_list.append(value['id'])
            # return default resource id if only one resource is available.
            if len(resources_list) == 1:
                print(' ')
                print("[MESSAGE] Using resource group "
                      "'{}'.".format(resources_name[0]))
                return resources_list[0]
            else:
                while True:
                    resources_id = input("[PROMPT] Your selection:  ").strip()
                    if not resources_id.isdigit() or \
                       int(resources_id) < 1 or \
                       int(resources_id) >= (len(resources_list) + 1):
                        print("[MESSAGE] Enter a number between 1 and "
                              "{}.".format(len(resources_name)))
                        continue
                    else:
                        break
                print('[MESSAGE] Selected resource is option '
                      '{}'.format(resources_id))
                return resources_list[int(resources_id) - 1]
        else:
            print("[DEBUG] Failing with status code:", response.status_code)
            print("[DEBUG] Reason for failure:", response.reason)
            sys.exit()

    def get_wml_deployment_details(self): # noqa
        """
        Get Watson Machine Learning deployment
        location, plan and resource plan id
        :return: WML location, plan and resource plan id
        """
        # WML available deployment locations.
        wml_deployment_location = ['eu-de', 'eu-gb', 'jp-tok', 'us-south']
        # WML available plans
        wml_plans = ['wml-lite', 'wml-professional', 'wml-standard']
        print("[MESSAGE] Choose a deployment location for this new instance.")
        for i, v in enumerate(wml_deployment_location, start=1):
            print('{:2d}. {}'.format(i, v))
        while True:
            wml_dep_option = input("[PROMPT] Your selection:  ").strip()
            if not wml_dep_option.isdigit() or \
               int(wml_dep_option) < 1 or \
               int(wml_dep_option) > len(wml_deployment_location):
                print("[MESSAGE] Enter a number between 1 and {}."
                      .format(len(wml_deployment_location)))
                continue
            else:
                print('---------------------------------------------'
                      '----------------------------')
                print('[MESSAGE] The Watson Machine Learning service instance'
                      ' will be created in "{}".'.
                      format(wml_deployment_location[int(wml_dep_option) - 1]))
                print('-----------------------------------------------'
                      '----------------------------')
                break
        print("[MESSAGE] Choose a Watson Machine Learning service plan:")
        for i, v in enumerate(wml_plans, start=1):
            print('{:2d}. {}'.format(i, v))
        while True:
            wml_plan_option = input("[PROMPT] Your selection:  ").strip()
            if not wml_plan_option.isdigit() or \
               int(wml_plan_option) < 1 or \
               int(wml_plan_option) > len(wml_plans):
                print("[MESSAGE] Enter a number between 1 and {}."
                      .format(len(wml_plans)))
                continue
            else:
                print('---------------------------------------------'
                      '-----------------------------')
                print('[MESSAGE] Using the "{}" service plan.'.
                      format(wml_plans[int(wml_plan_option) - 1]))
                print('----------------------------------------------'
                      '-----------------------------')
                break
        # Read config file to extract resource plan id
        with open('setup/config.json') as config_file:
            data = json.load(config_file)
        return wml_deployment_location[int(wml_dep_option) - 1], \
            wml_plans[int(wml_plan_option) - 1], \
            data["wml"][wml_plans[int(wml_plan_option) - 1]]

    def get_cos_deployment_details(self):
        """
        Get Cloud Object Storage deployment details
        :return: COS Plan and resource plan id
        """
        # Available COS plans
        cos_plans = ['cos-lite', 'cos-standard']
        print("[MESSAGE] Choose Cloud Object Storage plan "
              "from the displayed options. ")
        for i, v in enumerate(cos_plans, start=1):
            print('{:2d}. {}'.format(i, v))
        while True:
            cos_plan_option = input("[PROMPT] Your selection: ").strip()
            if not cos_plan_option.isdigit() or \
               int(cos_plan_option) < 1 or \
               int(cos_plan_option) > len(cos_plans):
                print("[MESSAGE] Enter a number between 1 and {}."
                      .format(len(cos_plans)))
                continue
            else:
                print('----------------------------------------------'
                      '--------------------------------')
                print('[MESSAGE] Chosen Cloud Object Storage plan is : '
                      '{}'.format(cos_plans[int(cos_plan_option) - 1]))
                print('-----------------------------------------------'
                      '-------------------------------')
                break
        # Read config file to extract resource plan id
        with open('setup/config.json') as config_file:
            data = json.load(config_file)
        return cos_plans[int(cos_plan_option) - 1], \
            data["cos"][cos_plans[int(cos_plan_option) - 1]]

    def service_create(self, instance_name, location, resource_id,
                       resource_plan_id):
        """
        Create IBM cloud service under provided resource.
        :param instance_name: new nstance name to be created
        :param location: location where instance needs to be created
        :param resource_id: Resource id under which instance
        needs to be created
        :param resource_plan_id: resource plan id
        :return: instance guid
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        data_instance = {
            "name": instance_name,
            "target": location,
            "resource_group": resource_id,
            "resource_plan_id": resource_plan_id,
        }
        response = requests.post("https://resource-controller.cloud.ibm.com"
                                 "/v2/resource_instances", headers=headers,
                                 json=data_instance)
        # Response error check
        if response.status_code == 201:
            response = response.json()
            print("[MESSAGE] Instance with the name '%s' "
                  "has been created" % response['name'])
            return response['guid']
        else:
            print("[DEBUG] Failing with status code:", response.status_code)
            print("[DEBUG] Reason for failure:", response.reason)
            sys.exit()

    def wml_key_create(self, wml_key_name, wml_instance_guid):
        """
        Create Watson Machine Learning key
        :param wml_key_name: new WML key name to be created
        :param wml_instance_guid: wml instance guid
        :return: WML apikey, url and instance_id.
                 Exit on error in key creation.
        """
        headers = {
            'Authorization': self.iam_access_token,
        }
        data_wml = {
            "name": wml_key_name,
            "source": wml_instance_guid,
        }
        # Instance create
        wml_key_response = requests.post('https://resource-controller.'
                                         'cloud.ibm.com/v2/resource_keys',
                                         headers=headers, json=data_wml)
        # Response error check
        if wml_key_response.status_code == 201:
            wml_key_response = wml_key_response.json()
            print("[MESSAGE] Service credentials named '{}' have been "
                  "created.".format(wml_key_response['name']))
            return wml_key_response['credentials']['apikey'], \
                wml_key_response['credentials']['instance_id'], \
                wml_key_response['credentials']['url']
        else:
            print("[DEBUG] Failing with status code:",
                  wml_key_response.status_code)
            print("[DEBUG] Reason for failure:",
                  wml_key_response.reason)
            sys.exit()

    def cos_key_create(self, cos_key_name, cos_instance_guid):
        """
        Create Cloud Object Storage key
        :param cos_key_name: new COS key name.
        :param cos_instance_guid: COS instance id
        :return: instance id, apikey, access key id and secret
        access key. Exit on error in key creation.
                 Exit on error in key creation.
        """
        hmac_value = True
        headers = {
            'Authorization': self.iam_access_token,
        }
        # Request body for key creation
        data_obj = {
            "name": cos_key_name,
            "source": cos_instance_guid,
            "parameters": {"HMAC": hmac_value},
            "role": "Writer"
        }
        # Key creation
        cos_key_response = requests.post('https://resource-controller.'
                                         'cloud.ibm.com/v2/resource_keys',
                                         headers=headers, json=data_obj)
        # Error check
        if cos_key_response.status_code == 201:
            cos_key_response = cos_key_response.json()
            print("[MESSAGE] Object storage credentials named '{}' "
                  "have been created".format(cos_key_response['name']))
            return cos_key_response['credentials']['resource_instance_id'], \
                cos_key_response['credentials']['apikey'], \
                cos_key_response['credentials']['cos_hmac_keys'][
                       'access_key_id'], \
                cos_key_response['credentials']['cos_hmac_keys'][
                       'secret_access_key']
        else:
            print("[DEBUG] Failing with status code:",
                  cos_key_response.status_code)
            print("[DEBUG] Reason for failure:",
                  cos_key_response.reason)
            sys.exit()
