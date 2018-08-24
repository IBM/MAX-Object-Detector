import pytest
import requests


def test_response():

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
