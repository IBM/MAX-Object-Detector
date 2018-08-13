from flask_restplus import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage

from config import MODEL_META_DATA
from core.backend import ModelWrapper, read_image

api = Namespace('model', description='Model information and inference operations')

model_meta = api.model('ModelMetadata', {
    'id': fields.String(required=True, description='Model identifier'),
    'name': fields.String(required=True, description='Model name'),
    'description': fields.String(required=True, description='Model description'),
    'license': fields.String(required=False, description='Model license')
})

@api.route('/metadata')
class Model(Resource):
    @api.doc('get_metadata')
    @api.marshal_with(model_meta)
    def get(self):
        '''Return the metadata associated with the model'''
        return MODEL_META_DATA


model_wrapper = ModelWrapper()

model_label = api.model('ModelLabel', {
    'id': fields.String(required=True, description='Class label identifier'),
    'name': fields.String(required=True, description='Class label'),
})

labels_response = api.model('LabelsResponse', {
    'count': fields.Integer(required=True, description='Number of class labels returned'),
    'labels': fields.List(fields.Nested(model_label), description='Class labels that can be predicted by the model')
})

@api.route('/labels')
class Labels(Resource):
    @api.doc('get_labels')
    @api.marshal_with(labels_response)
    def get(self):
        '''Return the list of labels that can be predicted by the model'''
        result = {}
        result['labels'] = model_wrapper.categories
        result['count'] = len(model_wrapper.categories)
        return result

label_prediction = api.model('LabelPrediction', {
    'label_id': fields.String(required=False, description='Class label identifier'),
    'label': fields.String(required=True, description='Class label'),
    'probability': fields.Float(required=True, description='Predicted probability for the class label'),
    'detection_box': fields.List(fields.Float(required=True), description='Coordinates of the bounding box for detected object. Format is an array of normalized coordinates (ranging from 0 to 1) in the form [ymin, xmin, ymax, xmax].')
})

predict_response = api.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted class labels, probabilities and bounding box for each detected object')
})

# set up parser for image input data
image_parser = api.parser()
image_parser.add_argument('image', type=FileStorage, location='files', required=True, help='An image file (encoded as PNG or JPG/JPEG)')
image_parser.add_argument('threshold', type=float, default=0.7, help='Probability threshold for including a detected object in the response in the range [0, 1] (default: 0.7). Lowering the threshold includes objects the model is less certain about.')

@api.route('/predict')
class Predict(Resource):

    @api.doc('predict')
    @api.expect(image_parser)
    @api.marshal_with(predict_response)
    def post(self):
        '''Make a prediction given input data'''
        result = {'status': 'error'}

        args = image_parser.parse_args()
        threshold = args['threshold']
        image_data = args['image'].read()
        image = read_image(image_data)
        label_preds = model_wrapper.predict(image, threshold)
        
        result['predictions'] = label_preds
        result['status'] = 'ok'

        return result
