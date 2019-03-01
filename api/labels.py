from maxfw.core import MAX_API, LabelsAPI
from flask_restplus import fields
from core.model import ModelWrapper

model_label = MAX_API.model('ModelLabel', {
    'id': fields.String(required=True, description='Class label identifier'),
    'name': fields.String(required=True, description='Class label'),
})

labels_response = MAX_API.model('LabelsResponse', {
    'count': fields.Integer(required=True, description='Number of class labels returned'),
    'labels': fields.List(fields.Nested(model_label), description='Class labels that can be predicted by the model')
})


class ModelLabelsAPI(LabelsAPI):

    model_wrapper = ModelWrapper()

    @MAX_API.doc('labels')
    @MAX_API.marshal_with(labels_response)
    def get(self):
        '''Return the list of labels that can be predicted by the model'''
        result = {}
        result['labels'] = self.model_wrapper.categories
        result['count'] = len(self.model_wrapper.categories)
        return result
