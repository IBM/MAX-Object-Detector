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
import sys
import ruamel.yaml
from setup.token_generate import TokenGenerate
from setup.service_handling import ServiceHandler
from setup.yaml_handling import YAMLHandler
from setup.setup_functions import InstanceHandler
from setup.instance_handling import MainHandler

setup_goal = """
Use this script to configure your environment for MAX model training:
 1. Manage Watson Machine Learning and Cloud Object Storage training resources.
 2. Set environment variables required for the model training script.
 3. Customize the training configuration file.
 4. Configure the training compute resources.
"""

print(setup_goal)

if len(sys.argv) == 1:
    print('Invocation error. '
          'Please provide a training configuration YAML file name.')
    print('\nUsage: python {} <training_config_file>  \n'
          .format(sys.argv[0]))
    sys.exit()

if len(sys.argv) == 2:
    if os.path.isfile(sys.argv[1]) is False:
        print('Invocation error. "{}" is not a file.'.format(sys.argv[1]))
        print('\nUsage: python {} <training_config_file>  \n'
              .format(sys.argv[0]))
        sys.exit()
    file_name = sys.argv[1]
    yaml = ruamel.yaml.YAML(typ='rt')
    yaml.allow_duplicate_keys = True
    yaml.preserve_quotes = True
    yaml.indent(mapping=6, sequence=4)
    try:
        with open(file_name) as fp:
            # Loading configuration file
            config = yaml.load(open(file_name))
            assert ("bucket" in config['train'][
                'data_source']['training_data'])
            assert ("bucket" in config['train'][
                'model_training_results']['trained_model'])
            assert ("path" in config['train'][
                'data_source']['training_data_local'])
            assert ("name" in config['train'][
                'execution']['compute_configuration'])
            assert ("path" in config['train']['data_source'][
                'training_data'])
    except Exception as e:
        print("Exception is: ", e)
        print("[ERROR] Provide a valid configuration YAML "
              "file for initiating the training process")
        sys.exit()


def yaml_handle(read_flag, input_bucket_name, local_directory,
                result_bucket_name, compute_config):
    """
    This function handles:

    1. Reading configuration variables from YAML file.
    2. Updating configuration variables to YAML file.
    3. Updating only compute configuration to YAML file.

    :param read_flag: indicator for choosing the operation
           to be performed.
    :param input_bucket_name: input bucket name
    :param local_directory: local directory from where data
           needs to be uploaded
    :param result_bucket_name: result bucket name
    :param compute_config: compute configuration
    :return:
      - Configuration variables if read flag is not set to 'Y'.
      - `True` after successful configuration changes.

    Exit on error in any of the steps.
    """
    file_name = sys.argv[1]
    yaml = ruamel.yaml.YAML(typ='rt')
    yaml.allow_duplicate_keys = True
    yaml.preserve_quotes = True
    yaml.indent(mapping=6, sequence=4)
    try:
        with open(file_name) as fp:
            # Loading configuration file
            config = yaml.load(open(file_name))
            # Reading configuration variables from configuration file.
            if read_flag == 'Y':
                cfg_inp_bucket = config['train']['data_source'][
                    'training_data']['bucket']
                cfg_out_bucket = config['train'][
                    'model_training_results']['trained_model'][
                    'bucket']
                cfg_loc_path = config['train']['data_source'][
                    'training_data_local']['path']
                cfg_cmp_config = config['train']['execution'][
                    'compute_configuration']['name']
                cfg_key_prefix = config['train']['data_source'][
                    'training_data']['path']
                return \
                    cfg_inp_bucket, cfg_out_bucket, cfg_loc_path, \
                    cfg_cmp_config, cfg_key_prefix
            if read_flag == 'N':
                with open(file_name, 'w') as fp:
                    config['train']['data_source'][
                        'training_data']['bucket'] = input_bucket_name
                    config['train']['model_training_results'][
                        'trained_model']['bucket'] = result_bucket_name
                    config['train']['data_source'][
                        'training_data_local']['path'] = local_directory
                    config['train']['execution'][
                        'compute_configuration']['name'] = compute_config
                    # Updating configuration file with new values
                    yaml.dump(config, fp)
                    return True
            if read_flag == 'C':
                with open(file_name, 'w') as fp:
                    # Updating configuration file with new compute
                    # configuration values.
                    config['train']['execution'][
                        'compute_configuration']['name'] = compute_config
                    yaml.dump(config, fp)
                    return True
    except Exception as ex:
        print(type(ex), '::', ex)
        sys.exit()


def env_extract(access_key, secret_access_key, apikey,
                instance_id, url):
    """
    This function:
    1. Extract current configuration values from the YAML file.
    2. Handle input and result buckets. Upload data to input
    bucket if necessary.
    3. Retrieve compute configuration value.
    4. Update YAML file with new values.
    5. Display environment variables value required to be set
    for initiating training process.
    :param access_key: cloud object storage access key.
    :param secret_access_key: cloud object storage secret access key
    :param apikey: watson machine learning apikey
    :param instance_id: watson machine learning instance id
    :param url: watson machine learning url

    The function exits by displaying environment variables value to be
    set along with configuration variables
    values that have been updated in YAML file.
    """
    (cfg_inp_bucket, cfg_out_bucket, cfg_loc_path, cfg_cmp_config,
     cfg_key_prefix) = yaml_handle('Y', '', '', '', '')
    yaml_handler = YAMLHandler(cfg_inp_bucket, cfg_out_bucket,
                               cfg_loc_path, cfg_cmp_config,
                               access_key, secret_access_key,
                               cfg_key_prefix)
    input_bucket_name, local_directory = yaml_handler.input_bucket_handle()
    result_bucket_name = yaml_handler.result_bucket_handle(input_bucket_name)
    compute_config = yaml_handler.configuration_check()

    summary = """
*-----------------------------------------------------------------------------*
| Model training setup is complete and your configuration file was updated.   |
*-----------------------------------------------------------------------------*

    Training data bucket name   : {}
    Local data directory        : {}
    Training results bucket name: {}
    Compute configuration       : {}

    """.format(input_bucket_name,
               local_directory,
               result_bucket_name,
               compute_config)

    print(summary)

    config_result = yaml_handle('N', input_bucket_name,
                                local_directory, result_bucket_name,
                                compute_config)
    if config_result:
        next_steps = """
*-----------------------------------------------------------------------------*
| Next steps                                                                  |
*-----------------------------------------------------------------------------*

1. Update or set the following environment variables:
    ML_APIKEY={}
    ML_INSTANCE={}
    ML_ENV={}
    AWS_ACCESS_KEY_ID={}
    AWS_SECRET_ACCESS_KEY={}

2. Run `python wml_train.py {} prepare` to verify your setup.

3. Run `python wml_train.py {} package` to train the model using your data.
        """.format(apikey,
                   instance_id,
                   url,
                   access_key,
                   secret_access_key,
                   sys.argv[1],
                   sys.argv[1])
        print(next_steps)
    sys.exit()


env_check = """

       *****    MODEL TRAINING ENVIRONMENT SETUP    *****

*********************    IBM Cloud access required  **********************
*                                                                        *
*  To configure your model training resources, this setup script         *
*  requires access to your IBM Cloud API key.                            *
*                                                                        *
*  You can create this key by following these steps:                     *
*       1. Open https://cloud.ibm.com/ in your browser and log in.       *
*       2. Go to Manage -> Access(IAM) -> IBM Cloud API Keys.            *
*       3. Click `Create an IBM Cloud API Key`. Provide `name` and       *
*           `description`.                                               *
*       4. Click `Create` and download the JSON Key file when prompted.  *
*       5. Save this file in a secure location.                          *
*                                                                        *
**************************************************************************

Checking for existing environment variables...

            """
print(env_check)
# Watson Machine Learning environment variables check flag
wml_env_check_flag = 'Y'
# Cloud Object Storage environment check flag
cos_env_check_flag = 'Y'
# Change setting flag
change_setting_flag = 'N'
# Checking WML environment variables
for env_var in ['ML_ENV', 'ML_APIKEY', 'ML_INSTANCE']:
    if os.environ.get(env_var) is None:
        wml_env_check_flag = 'N'
if wml_env_check_flag == 'N':
    print(' ')
    print('[MESSAGE] Watson Machine Learning environment variables '
          'are not defined.')
else:
    print('[MESSAGE] Watson Machine Learning environment variables '
          'are set.')
# Checking COS environment variables
for env_var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
    if os.environ.get(env_var) is None:
        cos_env_check_flag = 'N'
if cos_env_check_flag == 'N':
    print(' ')
    print('[MESSAGE] Cloud Object Storage environment variables '
          'are not defined.')
else:
    print('[MESSAGE] Cloud Object Storage environment variables '
          'are set.')

# steps to perform if environment variables are set
if cos_env_check_flag == 'Y' and wml_env_check_flag == 'Y':
    selection = """
*--------------------------------------------------------------------*
|     Choose an option from below for next steps                     |
|--------------------------------------------------------------------|
|                                                                    |
|    1. Update training configuration.                               |
|                                                                    |
|    2. Update environment variable and training configuration.      |
|                                                                    |
|    3. Update only the compute configuration.                       |
|                                                                    |
*--------------------------------------------------------------------*
            """
    print(selection)
    while True:
        # Get user option
        user_option = input("[PROMPT] Your selection:  ").strip()
        if not user_option.isdigit() or int(user_option) < 1 \
           or int(user_option) > 3:
            print("[MESSAGE] Enter a number between 1 and 3.")
            continue
        else:
            break
    # Steps for option 1: User wants to proceed with current settings.
    if user_option == '1':
        print('[MESSAGE] Proceeding with current settings.....')
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        wml_apikey = os.environ['ML_APIKEY']
        instance_id = os.environ['ML_INSTANCE']
        url = os.environ['ML_ENV']
        # update configuration values
        env_extract(access_key, secret_access_key, wml_apikey,
                    instance_id, url)
    # Steps for option 2: User wants to change the current settings.
    if user_option == '2':
        cos_env_check_flag = 'N'
        wml_env_check_flag = 'N'
        change_setting_flag = 'Y'
    # Steps for option 3: User wants to change only compute configuration.
    if user_option == '3':
        (cfg_inp_bucket, cfg_out_bucket, cfg_loc_path, cfg_cmp_config,
         cfg_key_prefix) = yaml_handle('Y', '', '', '', '')
        # Extract environment variables
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        # Call function to change configuration
        yaml_handler = YAMLHandler(cfg_inp_bucket, cfg_out_bucket,
                                   cfg_loc_path, cfg_cmp_config,
                                   access_key, secret_access_key,
                                   cfg_key_prefix)
        compute_config = yaml_handler.configuration_check()
        config_result = yaml_handle('C', '', '', '', compute_config)
        if config_result:
            print('-------------------------------------------------------'
                  '-----------------------')
            print("[MESSAGE] The compute configuration was changed to "
                  "'{}'.".format(compute_config))
            print('-------------------------------------------------------'
                  '-----------------------')
        next_steps = """
*-----------------------------------------------------------------------------*
| Next steps                                                                  |
*-----------------------------------------------------------------------------*

1. Run `python wml_train.py {} prepare` to verify your setup.

2. Run `python wml_train.py {} package` to train the model using your data.
        """.format(sys.argv[1],
                   sys.argv[1])
        print(next_steps)

        sys.exit()

resource_id_display = """
*--------------------------------------------------------------------------*
|                                                                          |
|   Retrieving your IBM resource group information.                        |
|                                                                          |
|   A resource group is used to organize your IBM Cloud resources, such    |
|   as AI and storage services.                                            |
|                                                                          |
*--------------------------------------------------------------------------*
                          """

config_display = """
*--------------------------------------------------------------------------*
|                                                                          |
|  To train a MAX model using your own data, an instance of the            |
|  Watson Machine Learning service and an instance of the Cloud Object     |
|  service is required.                                                    |
|                                                                          |
*--------------------------------------------------------------------------*
    """

# Steps for changing configuration
if cos_env_check_flag == 'N' or wml_env_check_flag == 'N':  # noqa
    flow_check_flag = 'N'
    if cos_env_check_flag == 'N' and wml_env_check_flag == 'N' and \
            change_setting_flag == 'N' and flow_check_flag == 'N':
        print('   ')
        print("*------------------------------------------------------"
              "-------------------------*")
        print("|  Configuring Watson Machine Learning and "
              "Cloud Object Storage resources.      |")
        print("*------------------------------------------------------"
              "-------------------------*")
        option = 'both'
        flow_check_flag = 'Y'

    if cos_env_check_flag == 'N' and change_setting_flag == 'N' \
            and flow_check_flag == 'N':
        selection = """
*---------------------------------------------------------------------------*
|    Change an existing model training configuration.                       |
|----------------------------------------------------------------------------
|                                                                           |
|    1. Re-configure Watson Machine Learning and Cloud Object Storage.      |
|                                                                           |
|    2. Re-configure only Cloud Object Storage.                             |
|                                                                           |
*---------------------------------------------------------------------------*
                           """
        print(selection)
        while True:
            option = input("[PROMPT] Your selection:  ")
            if not option.isdigit() or int(
                    option) < 1 or int(option) > 2:
                print("[MESSAGE] Enter a number 1 or 2.")
                continue
            else:
                if option == '1':
                    option = 'both'
                elif option == '2':
                    option = 'cos'
                flow_check_flag = 'Y'
                break

    if wml_env_check_flag == 'N' and change_setting_flag == 'N' \
            and flow_check_flag == 'N':
        selection = """
*---------------------------------------------------------------------------*
|    Change an existing model training configuration.                       |
|----------------------------------------------------------------------------
|                                                                           |
|    1. Re-configure Watson Machine Learning and Cloud Object Storage.      |
|                                                                           |
|    2. Re-configure only Watson Machine Learning.                          |
|                                                                           |
*---------------------------------------------------------------------------*
                           """
        print(selection)
        while True:
            option = input("[PROMPT] Your selection:  ")
            if not option.isdigit() or int(
                    option) < 1 or int(option) > 2:
                print("[MESSAGE] Enter a number 1 or 2.")
                continue
            else:
                if option == '1':
                    option = 'both'
                elif option == '2':
                    option = 'wml'
                flow_check_flag = 'Y'
                break

    if change_setting_flag == 'Y' and flow_check_flag == 'N':
        selection = """
*--------------------------------------------------------------------------*
|    Change an existing model training configuration.                      |
|--------------------------------------------------------------------------|
|                                                                          |
|    1. Re-configure Watson Machine Learning and Cloud Object Storage.     |
|                                                                          |
|    2. Re-configure only Watson Machine Learning.                         |
|                                                                          |
|    3. Re-configure only Cloud Object Storage.                            |
|                                                                          |
*--------------------------------------------------------------------------*
                   """
        print(selection)
        while True:
            option = input("[PROMPT] Your selection:  ")
            if not option.isdigit() or int(
                    option) < 1 or int(option) > 3:
                print("[MESSAGE] Enter a number between 1 and 3.")
                continue
            else:
                if option == '1':
                    option = 'both'
                elif option == '2':
                    option = 'wml'
                elif option == '3':
                    option = 'cos'
                flow_check_flag = 'Y'
                break
    # Pre-requisite check
    # Generating iam access token
    token_obj = TokenGenerate()
    iam_access_token = token_obj.get_api_location()

    #
    ins_obj = ServiceHandler(iam_access_token)
    # Retrieve resource id
    print(resource_id_display)
    resource_id = ins_obj.get_resources_id()
    ins_handle = InstanceHandler(iam_access_token)
    main_handle = MainHandler(resource_id, iam_access_token,
                              ins_obj, ins_handle)
    #
    print(config_display)
    # steps for configuring both COS and WML
    if option == 'both':
        try:
            # Retrieving WML details
            wml_apikey, instance_id, url = main_handle.wml_block()
        except KeyError as ex:
            print(type(ex), '::', ex)
            sys.exit()
        try:
            # Retrieving COS details
            resource_instance_id, apikey, access_key, secret_access_key = \
                main_handle.cos_block()
        except KeyError as ex:
            print(type(ex), '::', ex)
            sys.exit()
        # Updating config YAML file
        env_extract(access_key, secret_access_key, wml_apikey,
                    instance_id, url)
        sys.exit()
    # steps for configuring only WML
    if option == 'wml':
        try:
            # Retrieving WML details
            wml_apikey, instance_id, url = main_handle.wml_block()
        except KeyError:
            print("[DEBUG] Error in key retrieval details")
            sys.exit()
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        env_extract(access_key, secret_access_key, wml_apikey,
                    instance_id, url)
        sys.exit()
    # steps for configuring only COS
    if option == 'cos':
        try:
            resource_instance_id, apikey, access_key, secret_access_key = \
                main_handle.cos_block()
        except KeyError:
            print("Error in creating new COS key and retrieving details")
            sys.exit()
        print('***** Cloud Object Storage setting has been completed *****')
        wml_apikey = os.environ['ML_APIKEY']
        instance_id = os.environ['ML_INSTANCE']
        url = os.environ['ML_ENV']
        env_extract(access_key, secret_access_key, wml_apikey,
                    instance_id, url)
        sys.exit()
