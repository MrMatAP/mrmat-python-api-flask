#  MIT License
#
#  Copyright (c) 2021 MrMat
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import importlib.metadata
import sqlalchemy.orm
import flask
import flask_sqlalchemy
import flask_marshmallow
import flask_smorest
from .config import Config

try:
    __version__ = importlib.metadata.version('mrmat-python-api-flask')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'


class ORMBase(sqlalchemy.orm.DeclarativeBase):
    pass

app_config = Config.from_context()

app = flask.Flask(__name__)
app.config.setdefault('SQLALCHEMY_DATABASE_URI',app_config.db_url)
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
app.config.setdefault('SECRET_KEY', app_config.secret_key)
app.config.setdefault('API_TITLE', 'MrMat :: Python API :: Flask')
app.config.setdefault('API_VERSION', __version__)
app.config.setdefault('OPENAPI_VERSION', '3.0.2')
app.config.setdefault('OPENAPI_URL_PREFIX', '/')
app.config.setdefault('OPENAPI_SWAGGER_UI_PATH', '/swagger-ui')
app.config.setdefault('OPENAPI_SWAGGER_UI_URL', "https://cdn.jsdelivr.net/npm/swagger-ui-dist/")
app.config.setdefault('OPENAPI_REDOC_PATH', '/redoc')
app.config.setdefault('OPENAPI_REDOC_URL', "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js")
app.config.setdefault('OPENAPI_RAPIDOC_PATH', '/rapidoc')
app.config.setdefault('OPENAPI_RAPIDOC_URL', "https://unpkg.com/rapidoc/dist/rapidoc-min.js")

db = flask_sqlalchemy.SQLAlchemy(app, model_class=ORMBase)
ma = flask_marshmallow.Marshmallow(app)
api = flask_smorest.Api(app)

#
# Register APIs

from mrmat_python_api_flask.apis.healthz import api_healthz
api.register_blueprint(api_healthz, url_prefix='/api/healthz')

from mrmat_python_api_flask.apis.greeting.v1 import api_greeting_v1
api.register_blueprint(api_greeting_v1, url_prefix='/api/greeting/v1')

from mrmat_python_api_flask.apis.greeting.v2 import api_greeting_v2
api.register_blueprint(api_greeting_v2, url_prefix='/api/greeting/v2')

from mrmat_python_api_flask.apis.platform.v1 import api_platform_v1
api.register_blueprint(api_platform_v1, url_prefix='/api/platform/v1')

#
# Initialise the database

with app.app_context():
    db.create_all()
