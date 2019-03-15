# Flask settings
DEBUG = False

# Flask-restplus settings
RESTPLUS_MASK_SWAGGER = False

# Application settings

# API metadata
API_TITLE = 'MAX Object Detector'
API_DESC = 'Localize and identify multiple objects in a single image.'
API_VERSION = '1.1.0'

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
    'type': 'Object Detection',
    'source': 'https://developer.ibm.com/exchanges/models/all/max-object-detector/',
    'license': '{}'.format(MODEL_LICENSE)
}
