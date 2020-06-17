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

import pytest
import requests


def test_swagger():

    model_endpoint = 'http://localhost:5000/swagger.json'

    r = requests.get(url=model_endpoint)
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'application/json'

    json = r.json()
    assert 'swagger' in json
    assert json.get('info') and json.get('info').get('title') == 'MAX Object Detector'


def test_metadata():

    model_endpoint = 'http://localhost:5000/model/metadata'

    r = requests.get(url=model_endpoint)
    assert r.status_code == 200

    metadata = r.json()
    assert metadata['id'] == 'object-detector-ssd_mobilenet_v1'
    assert metadata['name'] == 'ssd_mobilenet_v1 TensorFlow Object Detector Model'
    assert metadata['description'] == 'ssd_mobilenet_v1 TensorFlow object detector model'
    assert metadata['type'] == 'Object Detection'
    assert metadata['source'] == 'https://developer.ibm.com/exchanges/models/all/max-object-detector/'
    assert metadata['license'] == 'ApacheV2'


def test_predict():
    model_endpoint = 'http://localhost:5000/model/predict'
    file_path = 'samples/a-pen-i-am.jpg'

    with open(file_path, 'rb') as file:
        file_form = {'image': (file_path, file, 'image/jpeg')}
        r = requests.post(url=model_endpoint, files=file_form)

    assert r.status_code == 200
    response = r.json()

    assert response['status'] == 'ok'
    # Training run uses fewer samples and epochs to train. Results have randomness due to this.
    # Checking for all the new classes used in the sample data.
    assert response['predictions'][0]['label'] in ('toy', 'pen')


if __name__ == '__main__':
    pytest.main([__file__])
