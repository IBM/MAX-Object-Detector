from maxfw.core import MAXApp
from api import ModelMetadataAPI, ModelPredictAPI

max_app = MAXApp()
max_app.add_api(ModelMetadataAPI, '/metadata')
max_app.add_api(ModelPredictAPI, '/predict')
max_app.run()
