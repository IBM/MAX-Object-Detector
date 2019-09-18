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
from pathlib import Path
import json


class TokenGenerate:
    """
    1. Prompt user to enter API Key JSON file.
       1.1 Check if the input path is a file, if not prompt again.
       1.2 Check if the input file is in JSON format, if not prompt again.
       1.3 Check if the input JSON file has `apikey`
       as one of its keys, if not prompt again.
    2. Generate IAM access token key.
    3. Exit for any error in key generation.
    4. Return IAM Access Token
    """

    def __init__(self):

        self.prompt = "[PROMPT] Enter IBM Cloud API Key " \
                      "JSON file location: "

    def get_api_location(self):
        """
        This function get cloud API key JSON file name from user
        and calls token generating function.
        :return: iam access token
        """

        def generate_token(api_key_value):
            """
            This function generates IBM Cloud access token
            :param key_file: IBM Cloud API Key JSON file
            :return: iam access token
            """
            headers_iam = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }

            data = {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": api_key_value,
            }
            key_response = requests.post("https://iam.cloud.ibm.com"
                                         "/identity/token",
                                         headers=headers_iam,
                                         data=data)
            if key_response.status_code == 200:
                # Storing access token
                key_response = key_response.json()
                iam_access_token = "Bearer " + key_response["access_token"]
                return iam_access_token
            else:
                print("[MESSAGE] !!! IAM Access Token creation failed !!! ")
                print("[MESSAGE] Failing with status code:",
                      key_response.status_code)
                print("[MESSAGE] Reason for failure:", key_response.reason)
                sys.exit()

        while True:
            try:
                location = input(self.prompt)
            except ValueError:
                print("[MESSAGE] Sorry, provide correct path of the key file.")
                continue

            if Path(location).is_file():
                try:
                    with open(location) as keyfile:
                        json_file_load = json.load(keyfile)
                        api_key_value = json_file_load["apiKey"],
                        iam_display = """
*----------------------------------------------------------------------------*
|                                                                            |
| Generating IAM Access Token using the provided key file.                   |
|                                                                            |
*----------------------------------------------------------------------------*
                        """
                        print(iam_display)
                        iam_access_token = generate_token(api_key_value)
                        break
                except Exception as e:
                    print("[MESSAGE] Enter valid JSON file")
                    if 'apiKey' in str(e):
                        print('[MESSAGE] JSON file has no {} key'.format(e))
                    continue
            else:
                print("[MESSAGE] Sorry, provide correct path of the key file")
                continue

        print('[MESSAGE] IAM Access Token has been generated.')
        return iam_access_token
