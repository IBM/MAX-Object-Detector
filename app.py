from maxfw.core import MAXApp
from api import ModelMetadataAPI, ModelLabelsAPI, ModelPredictAPI
from config import API_TITLE, API_DESC, API_VERSION

max_app = MAXApp(API_TITLE, API_DESC, API_VERSION)
max_app.add_api(ModelMetadataAPI, '/metadata')
max_app.add_api(ModelLabelsAPI, '/labels')
max_app.add_api(ModelPredictAPI, '/predict')
max_app.mount_static('/app/')
max_app.run()
