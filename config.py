import os
# Flask settings 
DEBUG = False

# Flask-restplus settings
RESTPLUS_MASK_SWAGGER = False

# Application settings

# API metadata
API_TITLE = 'Model Asset Exchange Server'
API_DESC = 'An API for serving models'
API_VERSION = '0.1'

# default model
# name of model to download
MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
DEFAULT_MODEL_PATH = 'assets'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
# Note:  This needs to be downloaded and/or compiled into pb format.
PATH_TO_CKPT = '{}/{}/frozen_inference_graph.pb'.format(DEFAULT_MODEL_PATH, MODEL_NAME)
PATH_TO_LABELS = '{}/{}/mscoco_label_map.pbtxt'.format(DEFAULT_MODEL_PATH, 'data')
NUM_CLASSES = 90

# for image models, may not be required
MODEL_INPUT_IMG_SIZE = (299, 299)
MODEL_LICENSE = 'ApacheV2'

MODEL_META_DATA = {
    'id': '{}-tf-mobilenet'.format(MODEL_NAME.lower()),
    'name': '{} TensorFlow Model'.format(MODEL_NAME),
    'description': '{} TensorFlow model trained on MobileNet'.format(MODEL_NAME),
    'type': 'object_detection',
    'license': '{}'.format(MODEL_LICENSE)
}
