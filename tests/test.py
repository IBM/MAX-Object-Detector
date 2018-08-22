import pytest
import pycurl
import io
import json


def test_response():
    c = pycurl.Curl()
    b = io.BytesIO()
    c.setopt(pycurl.URL, 'http://localhost:5000/model/predict')
    c.setopt(pycurl.HTTPHEADER, ['Accept:application/json', 'Content-Type: multipart/form-data'])
    c.setopt(pycurl.HTTPPOST, [('image', (pycurl.FORM_FILE, "assets/baby-bear.jpg"))])
    c.setopt(pycurl.WRITEFUNCTION, b.write)
    c.perform()
    assert c.getinfo(pycurl.RESPONSE_CODE) == 200
    c.close()

    response = b.getvalue()
    response = json.loads(response)

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
