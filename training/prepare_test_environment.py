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
from pathlib import Path

from ruamel.yaml import YAML
from utils.cos import COSWrapper

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
config['train']['data_source']['bucket'] = os.environ.get('COS_INPUT_BUCKET')
config['train']['data_source']['training_data']['bucket'] = os.environ.get('COS_INPUT_BUCKET')
# set output bucket
config['train']['model_training_results']['bucket'] = os.environ.get('COS_OUTPUT_BUCKET')
config['train']['model_training_results']['trained_model']['bucket'] = os.environ.get('COS_OUTPUT_BUCKET')

# save the file
with open(yaml_file, 'w') as fp:
    yaml.dump(config, fp)

# clear the input and output bucket
cw = COSWrapper(os.environ.get('AWS_ACCESS_KEY_ID'),
                os.environ.get('AWS_SECRET_ACCESS_KEY'))

cw.clear_bucket(os.environ.get('COS_INPUT_BUCKET'))
cw.clear_bucket(os.environ.get('COS_OUTPUT_BUCKET'))

# upload sample training data to the bucket
for fp in Path('sample_training_data/').glob('**/*'):
    fp = str(fp)
    if not os.path.isdir(fp):
        cw.upload_file(file_name=fp,
                       bucket_name=os.environ.get('COS_INPUT_BUCKET'),
                       key_name=fp.replace('sample_training_data/', ''))