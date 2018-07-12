import os
from flask import Flask
from api import api

if os.getenv('DISABLE_WEB_APP') != "true":
    app = Flask(__name__, static_url_path='')
else:
    app = Flask(__name__)

# load default config
app.config.from_object('config')
# load override config if exists
if 'APP_CONFIG' in os.environ:
    app.config.from_envvar('APP_CONFIG')
api.init_app(app)

if os.getenv('DISABLE_WEB_APP') != "true":
    @app.route('/app/')
    def web_app():
        return app.send_static_file('index.html')

if __name__ == '__main__':
        app.run(host='0.0.0.0')
