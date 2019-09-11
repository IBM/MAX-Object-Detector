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

################################################
#  THIS FILE IS ONLY USED FOR JENKINS TESTING  #
################################################

import os
import glob

import ibm_boto3
from ruamel.yaml import YAML

# verify that the environment variables are defined
assert 'COS_INPUT_BUCKET' in os.environ, 'Environment variable `COS_INPUT_BUCKET` is not defined.'
assert 'COS_OUTPUT_BUCKET' in os.environ, 'Environment variable `COS_OUTPUT_BUCKET` is not defined.'
assert 'AWS_ACCESS_KEY_ID' in os.environ, 'Environment variable `AWS_ACCESS_KEY_ID` is not defined.'
assert 'AWS_SECRET_ACCESS_KEY' in os.environ, 'Environment variable `AWS_SECRET_ACCESS_KEY` is not defined.'

# update the yaml file with the corresponding buckets
yaml_file = glob.glob('*.yaml')[0]

yaml = YAML(typ='rt')
yaml.allow_duplicate_keys = True
yaml.preserve_quotes = True
yaml.indent(mapping=6, sequence=4)

# open the file
with open(yaml_file, 'r') as fp:
    # Loading configuration file
    config = yaml.load(fp)

# set input bucket
config['train']['data_source']['training_data']['bucket'] = os.environ.get('COS_INPUT_BUCKET')
# set output bucket
config['train']['model_training_results']['trained_model']['bucket'] = os.environ.get('COS_OUTPUT_BUCKET')

# save the file
with open(yaml_file, 'w') as fp:
    yaml.dump(config, fp)

# clear the input and output bucket
cos = ibm_boto3.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                         endpoint_url="https://s3.us.cloud-object-storage.appdomain.cloud")

[x.delete() for x in cos.Bucket(os.environ.get('COS_INPUT_BUCKET')).objects.all()]
[x.delete() for x in cos.Bucket(os.environ.get('COS_OUTPUT_BUCKET')).objects.all()]
