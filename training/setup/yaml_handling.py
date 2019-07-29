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
from utils.cos import COSWrapper
import glob
import os


class YAMLHandler:

    def __init__(self, cfg_inp_bucket, cfg_out_bucket, cfg_loc_path,
                 cfg_cmp_config, access_key, secret_access_key,
                 cfg_key_prefix):
        assert access_key is not None, \
            'Parameter access key cannot be None'
        assert secret_access_key is not None, \
            'Parameter secret access key cannot be None'
        self.cfg_inp_bucket = cfg_inp_bucket
        self.cfg_out_bucket = cfg_out_bucket
        self.cfg_loc_path = cfg_loc_path
        self.cfg_cmp_config = cfg_cmp_config
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.cfg_key_prefix = cfg_key_prefix
        self.cos = COSWrapper(self.access_key, self.secret_access_key)

    def data_upload(self, bucket_name, path):
        """
        Upload data from the provided local directory to COS bucket
        :param bucket_name: input bucket name to which the data
        needs to be uploaded.
        :param path: local directory path from where data needs
        to be uploaded.
        :return: `True` if file has been uploaded successfully.
        `False` if file upload fails.
        """
        file_count = 0
        ignore_list = [(os.path.join(path, 'README.md'))]
        if (self.cfg_key_prefix != '' or self.cfg_key_prefix
                is not None):
            key_prefix = self.cfg_key_prefix
        else:
            key_prefix = None
        for file in glob.iglob(path + '/**/*', recursive=True):
            if file in ignore_list:
                continue
            if os.path.isfile(file):
                print(' [MESSAGE] Uploading "{}" to training data bucket '
                      '"{}" ...'.format(file, bucket_name))
                self.cos.upload_file(file,
                                     bucket_name,
                                     key_prefix,
                                     file[len(path):]
                                     .lstrip('/'))
                file_count += 1

        if file_count == 0:
            return False
        else:
            return True

    def get_directory(self):
        """
        This function prompts user to provide a local directory path from where
        data needs to be uploaded to the training input bucket.
        :return: local data directory path
        """
        while True:
            loc_dir = input("[PROMPT] Provided path is not a "
                            "directory. Enter path again: ")
            if loc_dir == '':
                print("[MESSAGE] 'None' provided as input. "
                      "Please provide directory path.")
                continue
            elif not os.path.isdir(loc_dir):
                print('[MESSAGE] Error. "{}" is not a directory '
                      'or cannot be accessed.'.
                      format(loc_dir))
                continue
            else:
                return loc_dir

    def local_directory_handle(self, bucket_name):
        """
        Handle data upload to the input bucket from local directory.
        1. If the path is configured in YAML file:
           1.1 Prompt user to decide if the configured path
           needs to be updated.
           1.2 Update if needed. Proceed if the user is fine
           with the current configuration.
           1.3 Proceed with the data upload.
        2. If the path is not configured in YAML file, prompt user
         input and proceed with data upload.
        :param bucket_name: input bucket name
        :return: data upload status and local directory path.
        """
        # Steps if local path is configured.
        if self.cfg_loc_path is not None:
            print('Local training data directory: {}'
                  .format(self.cfg_loc_path))
            user_data_opt = input("[PROMPT] Press 'Enter' to use this "
                                  "directory or specify a new path: ").strip()
            # If user press 'Enter', data will be uploaded from
            # the configured directory.
            if user_data_opt == '':
                user_data_opt = self.cfg_loc_path
            if not os.path.isdir(user_data_opt):
                local_directory = self.get_directory()
                return self.data_upload(
                        bucket_name, local_directory), local_directory
            else:
                return self.data_upload(bucket_name, user_data_opt), \
                       user_data_opt
        else:
            # Steps if local directory path has not been configured.
            print("[PROMPT] Local directory path from where input data needs "
                  "to be uploaded to the input "
                  "bucket is not configured. ")
            # User user to provide directory path.
            while True:
                local_directory = self.get_directory()
                return self.data_upload(
                    bucket_name, local_directory), local_directory

    def bucket_data_handling(self, bucket_name): # noqa
        """
        Handle Cloud Object Storage bucket data.
        1. If COS bucket is empty:
           1.1 Upload data.
           1.2 Proceed as it is with empty bucket.
        2. If COS bucket is not empty:
           2.1 Add data to the bucket
           2.2 Delete and add data to the bucket.
           2.3 Proceed with an existing data.
        :param bucket_name: bucket name
        :return: local directory path. Exit if data upload fails.
        """
        if self.cos.is_bucket_empty(bucket_name):
            print('----------------------------------------------------'
                  '------------------------')
            user_choice = input("[PROMPT] Bucket is empty. Enter 'Y' "
                                "to upload data from local directory "
                                "or press 'ENTER' if you don't want "
                                "to upload: ")
            if user_choice == 'Y' or user_choice.upper() == 'Y':
                handle_status, upload_path = \
                    self.local_directory_handle(bucket_name)
                if handle_status is False:
                    print('[MESSAGE] Error. No local training data was found '
                          'in the local directory.'.format(upload_path))
                    sys.exit()
                else:
                    print('[MESSAGE] Uploaded files to training data bucket '
                          '"{}".'.format(bucket_name))
                    return upload_path
            else:
                print("[MESSAGE] WARNING: Proceeding without data upload")
                if self.cfg_loc_path is not None:
                    return self.cfg_loc_path
                else:
                    return None
        else:
            options = """
*-----------------------------------------------------------------------------*
|              The selected training data bucket is not empty.                |
|-----------------------------------------------------------------------------|
|                                                                             |
|    1. Upload more training data to the bucket.                              |
|    2. Delete existing data and upload new training data to the bucket.      |
|    3. Use the existing data.                                                |
|                                                                             |
*-----------------------------------------------------------------------------*
                      """
            print(options)
            while True:
                user_choice = input("[PROMPT] Your selection: ").strip()
                if not user_choice.isdigit() or \
                   int(user_choice) < 1 or int(user_choice) > 3:
                    print("[MESSAGE] Enter a number between 1 and 3.")
                    continue
                else:
                    user_choice = int(user_choice)
                    # delete existing bucket content for option 2.
                    if user_choice == 2:
                        self.cos.clear_bucket(bucket_name)
                        print('[MESSAGE] Existing data was deleted.')
                    # upload data from directory.
                    if user_choice == 1 or user_choice == 2:
                        handle_status, upload_path = \
                            self.local_directory_handle(bucket_name)
                        if handle_status is False:
                            print('[MESSAGE] Error. No local training data '
                                  'was found in the local directory.'.
                                  format(upload_path))
                            sys.exit()
                        else:
                            print('[MESSAGE] Uploaded files to training '
                                  'data bucket "{}".'.format(bucket_name))
                            return upload_path
                    # proceed with existing data.
                    if user_choice == 3 and self.cfg_loc_path is None:
                        print("[MESSAGE] WARNING!!! Local directory not "
                              "configured. Proceeding with existing input "
                              "COS bucket data. ")
                        return None
                    if user_choice == 3 and self.cfg_loc_path is not None:
                        print('[MESSAGE] Existing training data will be used.')
                        return self.cfg_loc_path

    def bucket_list(self):
        """
        Get list of existing Cloud Object Storage buckets.
        :return: available bucket list, user option and number of buckets.
        """
        bucket_list = self.cos.get_bucket_list()
        if len(bucket_list) > 0:
            print('----------------------------------------------'
                  '------------------------')
            print('Choose an existing Cloud Object Storage bucket or '
                  'create a new bucket:')
            print('----------------------------------------------'
                  '------------------------')
            for ind, value in enumerate(bucket_list, start=1):
                print("{:2d}. {}".format(ind, value))
                if value == bucket_list[-1]:
                    print('{:2d}. {}'.format(int(ind) + 1,
                                             '* Create New Bucket *'))
            # User prompt
            while True:
                input_new_bucket = input("[PROMPT] Your selection : ").strip()
                if not input_new_bucket.isdigit() or \
                   int(input_new_bucket) < 1 or \
                   int(input_new_bucket) > (len(bucket_list) + 1):
                    print("[MESSAGE] Enter a number between 1 and "
                          "{}.".format(len(bucket_list) + 1))
                    continue
                else:
                    return len(bucket_list), input_new_bucket, bucket_list
        else:
            print('---------------------------------------------------'
                  '------------------------')
            print('No buckets are defined.')
            print('---------------------------------------------------'
                  '------------------------')
            return len(bucket_list), None, None

    def get_new_input_bucket(self, bucket_list, bucket_list_length):
        """
        Prompt user for new input bucket name.
        :param bucket_list: existing bucket list
        :param bucket_list_length: number of buckets.
        :return: new input bucket name and local directory path
                 from where the data was uploaded.
        """
        while True:
            try:
                new_input_bucket_name = input("[PROMPT] Please "
                                              "enter a new "
                                              "training data "
                                              "bucket name: ")
                if new_input_bucket_name == '':
                    print("[MESSAGE] A bucket name is required.")
                    continue
                elif self.cfg_out_bucket == new_input_bucket_name:
                    print("[MESSAGE] Entered bucket name is same "
                          "as configured training result bucket "
                          "name. Please provide a new name.")
                    continue
                elif bucket_list_length != 0 \
                        and new_input_bucket_name in bucket_list:
                    print("[MESSAGE] A bucket with this name already "
                          "exists.")
                    continue
                else:
                    result = self.cos.create_bucket(
                        new_input_bucket_name, exist_ok=True)
            except KeyboardInterrupt:
                sys.exit()
            except (ValueError, TypeError):
                print("[MESSAGE] Enter a valid training input"
                      " data bucket name")
                continue
            if result is True:
                print("[MESSAGE] Bucket {} has been created".
                      format(new_input_bucket_name))
                local_directory_path = self.bucket_data_handling(
                    new_input_bucket_name)
                return new_input_bucket_name, local_directory_path
            else:
                print("[MESSAGE] Enter a valid training input "
                      "data bucket name")
                continue

    def input_bucket_handle(self):  # noqa
        """
        Handle input bucket data.
        1. If input bucket is not configured.
           1.1 Get list of available buckets.
           1.2 If there is no existing bucket or if user decides to
           create new bucket, prompt user for new bucket name.
               Create new bucket and upload data.
           1.3 If user selects any existing bucket, proceed to data handling.
        2. If input bucket is configured.
           2.1 If user wants to proceed with the existing setting,
           try creating the bucket. If bucket exists, proceed
               to data handling.If bucket does not exist, prompt user new
               bucket name and proceed to data handling.
           2.2 If user wants to change the current settings, display all
           available buckets and let user choose one. Then
               proceed with data handling.
        :return: new input bucket name, local directory path. 'None`
        for any error in the process.
        """

        message = """
*----------------------------------------------------------------------------*
|                                                                            |
| Before you can train a model you need to upload training data to a         |
| bucket in your selected Cloud Object Storage service instance.             |
|                                                                            |
*----------------------------------------------------------------------------*
        """
        print(message)

        if self.cfg_inp_bucket is None:
            while True:
                # Get list of available buckets.
                bucket_list_length, input_new_bucket, bucket_list = \
                    self.bucket_list()
                # No available bucket or user wants to create a new bucket
                if bucket_list_length == 0 or (int(input_new_bucket) > 0 and
                                               int(input_new_bucket) ==
                                               (bucket_list_length + 1)):
                    # get new bucket name
                    return self.get_new_input_bucket(
                        bucket_list, bucket_list_length)
                elif (int(input_new_bucket) != (bucket_list_length + 1) and
                      bucket_list[int(input_new_bucket) - 1] ==
                      self.cfg_out_bucket):
                    print("[MESSAGE] Selected bucket has been configured as "
                          "the result bucket. Please choose a different "
                          "bucket or create a new bucket")
                    continue
                # Using the existing bucket
                elif int(input_new_bucket) != (bucket_list_length + 1):
                    config_inp_bucket = bucket_list[int(input_new_bucket) - 1]
                    print("[MESSAGE] Using existing bucket '{}' "
                          "as training data bucket. "
                          .format(config_inp_bucket))
                    local_directory_path = self.bucket_data_handling(
                        config_inp_bucket)
                    return config_inp_bucket, local_directory_path
                else:
                    print("[DEBUG] Error in handling input COS bucket")
                    return None, None
        else:
            # Steps if bucket is configured.
            print("Training data bucket:  {} ".
                  format(self.cfg_inp_bucket))
            bucket_list = self.cos.get_bucket_list()
            # prompt user input
            cfg_option = input("[PROMPT] Press 'ENTER' to use the currently "
                               "selected bucket. To select a different "
                               "enter"
                               " 'Y': ").strip().upper()
            if cfg_option == 'Y' and len(bucket_list) == 0:
                cfg_option = ''
            # Steps to follow if user wants to proceed with current settings.
            if cfg_option == '':
                try:
                    result = self.cos.create_bucket(self.cfg_inp_bucket,
                                                    exist_ok=True)
                except ValueError:
                    # get new bucket name if bucket does not exist
                    print("[MESSAGE] Bucket with the entered name is in "
                          "namespace.")
                    # get new bucket name
                    return self.get_new_input_bucket(
                        bucket_list, len(bucket_list))
                else:
                    # if bucket exists
                    if result is True and \
                            self.cfg_out_bucket != self.cfg_inp_bucket:
                        print("[MESSAGE] Training data will be loaded "
                              "from bucket '{}'".
                              format(self.cfg_inp_bucket))
                        local_directory_path = self.bucket_data_handling(
                            self.cfg_inp_bucket)
                        return self.cfg_inp_bucket, local_directory_path
                    if result is True and \
                            self.cfg_out_bucket == self.cfg_inp_bucket:
                        print("[MESSAGE] Training input and result bucket "
                              "names are same.")
                        return self.get_new_input_bucket(
                            bucket_list, len(bucket_list))
            # Steps to follow if user wants to change the current settings.
            elif (cfg_option.upper() == 'Y'
                  or cfg_option == 'Y') and len(bucket_list) != 0:
                while True:
                    bucket_list_length, input_new_bucket, bucket_list = \
                        self.bucket_list()
                    if int(input_new_bucket) == (bucket_list_length + 1):
                        return self.get_new_input_bucket(
                            bucket_list, bucket_list_length)
                    if self.cfg_out_bucket == bucket_list[int(
                            input_new_bucket) - 1]:
                        print("[MESSAGE] Bucket has been chosen for "
                              "storing results. Provide a valid option.")
                        continue
                    if int(input_new_bucket) != (bucket_list_length + 1):
                        print("[MESSAGE] Bucket {} is ready for use. "
                              "Proceeding with further configuration".format(
                                bucket_list[int(input_new_bucket) - 1]))
                        local_directory_path = self.bucket_data_handling(
                            bucket_list[int(input_new_bucket) - 1])
                        return bucket_list[int(input_new_bucket) - 1], \
                            local_directory_path
            else:
                print("[MESSAGE] Invalid option entered. "
                      "Please check and start again.")
                return None, None

    def delete_result_bucket(self, result_bucket):
        """
        Deletes result bucket contents if user wants to.
        :param result_bucket: result bucket name.
        """
        if self.cos.is_bucket_empty(result_bucket) is False:

            options = """
*-----------------------------------------------------------------------------*
|              The selected training results bucket is not empty.             |
|-----------------------------------------------------------------------------|
|                                                                             |
|    1. Delete objects in this bucket.                                        |
|    2. Keep objects in this bucket.                                          |
|                                                                             |
*-----------------------------------------------------------------------------*
            """
            print(options)
            while True:
                bucket_clean_choice = input("[PROMPT] Your selection: ") \
                                      .strip()
                if not bucket_clean_choice.isdigit() or \
                   int(bucket_clean_choice) < 1 or \
                   int(bucket_clean_choice) > 2:
                    print("[MESSAGE] Enter 1 or 2.")
                    continue
                if int(bucket_clean_choice) == 1:
                    self.cos.clear_bucket(result_bucket)
                break

    def new_bucket_creation(self, input_bucket_name):  # noqa
        """
        1. Prompt user a new bucket name, if there is no existing
        bucket or user selects option to create a new bucket.
           User will be prompted to enter new name till it gets
           unique bucket name and successful bucket creation.
        2. For other options, retrieve bucket name corresponding
        to the chosen option.
        :param bucket_list_length: number of available buckets.
        :param input_new_bucket: User choice
        :param bucket_list: list containing existing bucket names.
        :return: result bucket name. `None` for any error in process.
        """

        while True:
            try:
                new_input_bucket_name = \
                    input("[PROMPT] Please enter a "
                          "new name for result bucket: ")
                if input_bucket_name == new_input_bucket_name:
                    print("[MESSAGE] Input and result bucket "
                          "names can not be same. Enter a "
                          "valid result bucket name.")
                    continue
                elif new_input_bucket_name == '':
                    print("[MESSAGE] Bucket name is required")
                    continue
                else:
                    result_bucket_check = \
                        self.cos.create_bucket(
                            new_input_bucket_name, exist_ok=True)
            except KeyboardInterrupt:
                sys.exit()
            except (ValueError, TypeError):
                print("[MESSAGE] Enter a valid result bucket"
                      " name.")
                continue
            if result_bucket_check is True:
                print("[MESSAGE] Bucket {} has been "
                      "created".format(new_input_bucket_name))
                return new_input_bucket_name
            else:
                print("[MESSAGE] Enter a valid "
                      "result bucket name.")
                continue

    def result_bucket_handle(self, input_bucket_name):  # noqa
        """
        Handle result bucket.
        1. If result bucket is not configured:
           1.1 Prompt user either to select a bucket name from
           the list of available buckets or choose option to create
               a new bucket.
           1.2 Handle user choice.
        2. If result bucket is configured.
           2.1 Try creating the bucket. If it returns a `ValueError`,
           prompt user to enter a new bucket name.
           2.2 Handle result bucket data if the creation is successful.
        :param input_bucket_name: data input bucket name
        :return: result bucket name. `None` for any error in process.
        """
        message = """
*----------------------------------------------------------------------------*
|                                                                            |
| Model training results will be stored in a bucket in your selected         |
| Cloud Object Storage service instance.                                     |
|                                                                            |
*----------------------------------------------------------------------------*
        """
        print(message)
        if self.cfg_out_bucket is None:
            while True:
                bucket_list_length, input_new_bucket, bucket_list \
                    = self.bucket_list()
                if int(input_new_bucket) != bucket_list_length + 1:
                    if bucket_list[int(input_new_bucket) - 1] \
                            == input_bucket_name:
                        print("[MESSAGE] Training data and training results "
                              "must be stored in different buckets. ")
                        continue
                    else:
                        break
                else:
                    break

            if bucket_list_length == 0 or \
                    (int(input_new_bucket) > 0 and
                     int(input_new_bucket) == (bucket_list_length + 1)):
                while True:
                    result_bucket = \
                        input("[PROMPT] Enter a new "
                              "result bucket name: ").strip()
                    if result_bucket == '':
                        continue
                    elif bucket_list_length != 0 and \
                            result_bucket in bucket_list:
                        print("[MESSAGE] A bucket with this name "
                              "already exists.")
                        continue
                    else:
                        try:
                            create_status = self.cos.create_bucket(
                                result_bucket)
                        except (ValueError, TypeError):
                            return self.new_bucket_creation(
                                input_bucket_name)
                        if create_status:
                            print("[MESSAGE] Training results bucket '{}' "
                                  "is created".format(result_bucket))
                            return result_bucket
                        else:
                            print("[MESSAGE] Error creating bucket "
                                  "{}.".format(result_bucket))
                            continue
            elif int(input_new_bucket) != (bucket_list_length + 1):
                result_bucket = bucket_list[int(input_new_bucket) - 1]
                self.delete_result_bucket(result_bucket)
                return result_bucket
            else:
                print("[DEBUG] Invalid Entry")
                return None
        else:
            print("Configured results bucket:  `{}` ".
                  format(self.cfg_out_bucket))
            if self.cfg_out_bucket == input_bucket_name:
                print("[MESSAGE] Input and result buckets are same")
                return self.new_bucket_creation(
                    input_bucket_name)
            else:
                try:
                    result_bucket_check = \
                        self.cos.create_bucket(
                            self.cfg_out_bucket, exist_ok=True)
                except (ValueError, TypeError):
                    print("[MESSAGE] Bucket with the entered name "
                          "is in namespace. ")
                    return self.new_bucket_creation(
                        input_bucket_name)
                else:
                    if result_bucket_check:
                        print("[MESSAGE] Bucket {} "
                              "exists.". format(
                               self.cfg_out_bucket))
                        self.delete_result_bucket(self.cfg_out_bucket)
                        return self.cfg_out_bucket

    def configuration_check(self):
        """
        Handle compute configuration setting.
        1. If configured, prompt user whether to proceed with
        same configuration or modify existing config. Prompt
           user to choose from displayed option, if user wishes
           to update the setting.
        2. If not configured, prompt user to choose from the displayed options.
        :return: compute configuration.
        """

        options = """
*-----------------------------------------------------------------------------*
| A compute tier configures the GPU resources that the Watson Machine         |
| Learning service instance can utilize during model training.                |
|                                                                             |
| Note: The v100 and v100x2 tiers are not available for lite plan instances.  |
*-----------------------------------------------------------------------------*
            """
        print(options)
        print('\nPick a compute configuration.')

        compute_tiers = ['k80', 'k80x2', 'k80x4', 'v100', 'v100x2']
        for ind, value in enumerate(compute_tiers, start=1):
            if self.cfg_cmp_config == value:
                print("{:2d}. {} (selected)".format(ind, value))
            else:
                print("{:2d}. {}".format(ind, value))

        while True:
            compute_tier = input("[PROMPT] Your selection: ").strip()
            if compute_tier == '':
                if self.cfg_cmp_config is not None:
                    return self.cfg_cmp_config
                else:
                    print("[MESSAGE] Enter a number between 1 and "
                          "{}.".format(len(compute_tiers)))
                continue
            else:
                if not compute_tier.isdigit() or int(compute_tier) < 1 or \
                   int(compute_tier) > len(compute_tiers):
                    print("[MESSAGE] Enter a number between 1 and "
                          "{}.".format(len(compute_tiers)))
                    continue
                else:
                    return compute_tiers[int(compute_tier) - 1]
