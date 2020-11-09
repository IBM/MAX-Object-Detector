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
    model = os.getenv('MODEL')
    assert metadata['id'] == f'object-detector-{model}'
    assert metadata['name'] == f'{model} TensorFlow Object Detector Model'
    assert metadata['description'] == f'{model} TensorFlow object detector model'
    assert metadata['type'] == 'Object Detection'
    assert metadata['source'] == 'https://developer.ibm.com/exchanges/models/all/max-object-detector/'
    assert metadata['license'] == 'ApacheV2'


def test_predict():
    model_endpoint = 'http://localhost:5000/model/predict'
    file_path = 'samples/baby-bear.jpg'

    with open(file_path, 'rb') as file:
        file_form = {'image': (file_path, file, 'image/jpeg')}
        r = requests.post(url=model_endpoint, files=file_form)

    assert r.status_code == 200
    response = r.json()

    assert response['status'] == 'ok'

    # One is Teddy Bear and the other is Child
    assert frozenset((response['predictions'][0]['label_id'],
                      response['predictions'][1]['label_id'])) == frozenset(('1', '88'))

    #  Teddy Bear
    bear_index = 0 if response['predictions'][0]['label_id'] == '88' else 1
    assert response['predictions'][bear_index]['label_id'] == '88'
    assert response['predictions'][bear_index]['label'] == 'teddy bear'
    assert response['predictions'][bear_index]['probability'] > 0.95

    assert response['predictions'][bear_index]['detection_box'][0] > 0.25
    assert response['predictions'][bear_index]['detection_box'][0] < 0.3

    assert response['predictions'][bear_index]['detection_box'][1] > 0.5
    assert response['predictions'][bear_index]['detection_box'][1] < 0.6

    assert response['predictions'][bear_index]['detection_box'][2] > 0.6
    assert response['predictions'][bear_index]['detection_box'][2] < 0.7

    assert response['predictions'][bear_index]['detection_box'][3] > 0.8
    assert response['predictions'][bear_index]['detection_box'][3] < 0.9

    # Child
    child_index = 0 if bear_index == 1 else 1
    assert response['predictions'][child_index]['label_id'] == '1'
    assert response['predictions'][child_index]['label'] == 'person'
    assert response['predictions'][child_index]['probability'] > 0.95

    assert response['predictions'][child_index]['detection_box'][0] > 0.2
    assert response['predictions'][child_index]['detection_box'][0] < 0.3

    assert response['predictions'][child_index]['detection_box'][1] > 0.2
    assert response['predictions'][child_index]['detection_box'][1] < 0.3

    assert response['predictions'][child_index]['detection_box'][2] > 0.6
    assert response['predictions'][child_index]['detection_box'][2] < 0.7

    assert response['predictions'][child_index]['detection_box'][3] > 0.5
    assert response['predictions'][child_index]['detection_box'][3] < 0.6


def test_predict_non_image():
    model_endpoint = 'http://localhost:5000/model/predict'
    file_path = 'requirements.txt'

    with open(file_path, 'rb') as file:
        file_form = {'image': (file_path, file, 'image/jpeg')}
        r = requests.post(url=model_endpoint, files=file_form)

    assert r.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__])
