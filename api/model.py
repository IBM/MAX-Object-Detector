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
    'id': fields.String(required=True, description='Label identifier'),
    'name': fields.String(required=True, description='Label'),
})

labels_response = api.model('LabelsResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'labels': fields.List(fields.Nested(model_label), description='Labels that can be predicted by the model')
})

@api.route('/labels')
class Labels(Resource):
    @api.doc('get_labels')
    @api.marshal_with(labels_response)
    def get(self):
        '''Return the list of labels that can be predicted by the model'''
        result = {'status': 'error'}

        result['labels'] = model_wrapper.categories
        result['status'] = 'ok'

        return result

label_prediction = api.model('LabelPrediction', {
    'label_id': fields.String(required=False, description='Label identifier'),
    'label': fields.String(required=True, description='Class label'),
    'probability': fields.Float(required=True),
    'detection_box': fields.List(fields.Float(required=True))
})

predict_response = api.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted labels and probabilities')
})

# set up parser for image input data
image_parser = api.parser()
image_parser.add_argument('image', type=FileStorage, location='files', required=True)
image_parser.add_argument('threshold', type=float, default=0.7)

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
