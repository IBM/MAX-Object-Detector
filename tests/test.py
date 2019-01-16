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
    assert metadata['id'] == 'ssd_mobilenet_v1_coco_2017_11_17-tf-mobilenet'
    assert metadata['name'] == 'ssd_mobilenet_v1_coco_2017_11_17 TensorFlow Model'
    assert metadata['description'] == 'ssd_mobilenet_v1_coco_2017_11_17 TensorFlow model trained on MobileNet'
    assert metadata['type'] == 'Object Detection'
    assert metadata['source'] == 'https://developer.ibm.com/exchanges/models/all/max-object-detector/'
    assert metadata['license'] == 'ApacheV2'


def test_predict():
    model_endpoint = 'http://localhost:5000/model/predict'
    file_path = 'assets/baby-bear.jpg'

    with open(file_path, 'rb') as file:
        file_form = {'image': (file_path, file, 'image/jpeg')}
        r = requests.post(url=model_endpoint, files=file_form)

    assert r.status_code == 200
    response = r.json()

    assert response['status'] == 'ok'

    #  Teddy Bear
    assert response['predictions'][0]['label_id'] == '88'
    assert response['predictions'][0]['label'] == 'teddy bear'
    assert response['predictions'][0]['probability'] > 0.95

    assert response['predictions'][0]['detection_box'][0] > 0.25
    assert response['predictions'][0]['detection_box'][0] < 0.3

    assert response['predictions'][0]['detection_box'][1] > 0.5
    assert response['predictions'][0]['detection_box'][1] < 0.6

    assert response['predictions'][0]['detection_box'][2] > 0.6
    assert response['predictions'][0]['detection_box'][2] < 0.7

    assert response['predictions'][0]['detection_box'][3] > 0.8
    assert response['predictions'][0]['detection_box'][3] < 0.9

    # Child
    assert response['predictions'][1]['label_id'] == '1'
    assert response['predictions'][1]['label'] == 'person'
    assert response['predictions'][1]['probability'] > 0.95

    assert response['predictions'][1]['detection_box'][0] > 0.2
    assert response['predictions'][1]['detection_box'][0] < 0.3

    assert response['predictions'][1]['detection_box'][1] > 0.2
    assert response['predictions'][1]['detection_box'][1] < 0.3

    assert response['predictions'][1]['detection_box'][2] > 0.6
    assert response['predictions'][1]['detection_box'][2] < 0.7

    assert response['predictions'][1]['detection_box'][3] > 0.5
    assert response['predictions'][1]['detection_box'][3] < 0.6


if __name__ == '__main__':
    pytest.main([__file__])
