from maxfw.core import MAX_API, PredictAPI
from flask_restplus import fields
from werkzeug.datastructures import FileStorage
from core.model import ModelWrapper

input_parser = MAX_API.parser()
input_parser.add_argument('image', type=FileStorage, location='files', required=True,
                          help='An image file (encoded as PNG or JPG/JPEG)')
input_parser.add_argument('threshold', type=float, default=0.7,
                          help='Probability threshold for including a detected object in the response in the range [0, 1] (default: 0.7). Lowering the threshold includes objects the model is less certain about.')


label_prediction = MAX_API.model('LabelPrediction', {
    'label_id': fields.String(required=False, description='Class label identifier'),
    'label': fields.String(required=True, description='Class label'),
    'probability': fields.Float(required=True, description='Predicted probability for the class label'),
    'detection_box': fields.List(fields.Float(required=True), description='Coordinates of the bounding box for detected object. Format is an array of normalized coordinates (ranging from 0 to 1) in the form [ymin, xmin, ymax, xmax].')
})

predict_response = MAX_API.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted class labels, probabilities and bounding box for each detected object')
})


class ModelPredictAPI(PredictAPI):

    model_wrapper = ModelWrapper()

    @MAX_API.doc('predict')
    @MAX_API.expect(input_parser)
    @MAX_API.marshal_with(predict_response)
    def post(self):
        """Make a prediction given input data"""
        result = {'status': 'error'}

        args = input_parser.parse_args()
        threshold = args['threshold']
        image_data = args['image'].read()
        image = self.model_wrapper._read_image(image_data)
        label_preds = self.model_wrapper._predict(image, threshold)

        result['predictions'] = label_preds
        result['status'] = 'ok'

        return result
