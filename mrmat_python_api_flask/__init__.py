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

"""Main entry point when executing this application as a WSGI app
"""

import sys
import os
import importlib.metadata
from logging.config import dictConfig

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect
from flask_smorest import Api

try:
    __version__ = importlib.metadata.version('mrmat-python-api-flask')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package. Likely because you are still hacking on it
    __version__ = '0.0.0.dev0'

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
oidc = OpenIDConnect()
api = Api()

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    },
    'mrmat_python_api_flask': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


def create_app(config_override=None, instance_path=None):
    """Factory method to create a Flask app.

    Allows configuration overrides by providing the optional test_config dict as well as a `config.py`
    within the instance_path. Will create the instance_path if it does not exist. instance_path is meant
    to be outside the package directory.

    Args:
        config_override: Optional dict to override configuration
        instance_path: Optional fully qualified path to instance directory (for configuration etc)

    Returns: an initialised Flask app object

    """
    app = Flask(__name__,
                static_url_path='',
                static_folder='static',
                instance_relative_config=True,
                instance_path=instance_path)

    #
    # Set configuration defaults. If a config file is present then load it. If we have overrides, apply them

    app.config.setdefault('SECRET_KEY', os.urandom(16))
    app.config.setdefault('SQLALCHEMY_DATABASE_URI',
                          'sqlite+pysqlite:///' + os.path.join(app.instance_path, 'mrmat-python-api-flask.sqlite'))
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('OIDC_USER_INFO_ENABLED', True)
    app.config.setdefault('OIDC_RESOURCE_SERVER_ONLY', True)
    app.config.setdefault('API_TITLE', 'MrMat :: Python :: API :: Flask')
    app.config.setdefault('API_VERSION', __version__)
    app.config.setdefault('OPENAPI_VERSION', '3.0.2')
    app.config.setdefault('OPENAPI_URL_PREFIX', '/apidoc')
    app.config.setdefault('OPENAPI_JSON_PATH', 'openapi.json')
    app.config.setdefault('OPENAPI_SWAGGER_UI_PATH', 'swagger')
    app.config.setdefault('OPENAPI_SWAGGER_UI_URL', 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/')
    app.config.setdefault('OPENAPI_REDOC_PATH', 'redoc')
    app.config.setdefault('OPENAPI_REDOC_URL', 'https://rebilly.github.io/ReDoc/releases/latest/redoc.min.js')
    app.config.setdefault('OPENAPI_RAPIDOC_PATH', 'rapidoc')
    app.config.setdefault('OPENAPI_RAPIDOC_URL', 'https://unpkg.com/rapidoc/dist/rapidoc-min.js')
    app.config.setdefault('OPENAPI_SWAGGER_UI_CONFIG', {
        'oauth2RedirectUrl': 'http://localhost:5000/apidoc/swagger/oauth2-redirect'
    })
    app.config.setdefault('OPENAPI_SWAGGER_UI_ENABLE_OAUTH', True)
    if 'FLASK_CONFIG' in os.environ and os.path.exists(os.path.expanduser(os.environ['FLASK_CONFIG'])):
        app.config.from_json(os.path.expanduser(os.environ['FLASK_CONFIG']))
    if config_override is not None:
        app.config.from_mapping(config_override)

    #
    # Create the instance folder if it does not exist

    try:
        if not os.path.exists(app.instance_path):
            app.logger.info(f'Creating new instance path at {app.instance_path}')
            os.makedirs(app.instance_path)
        else:
            app.logger.info(f'Using existing instance path at {app.instance_path}')
    except OSError:
        app.logger.error(f'Failed to create new instance path at {app.instance_path}')
        sys.exit(1)

    # When using Flask-SQLAlchemy, there is no need to explicitly import DAO classes because they themselves
    # inherit from the SQLAlchemy model

    global db, ma, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    api.init_app(app)
    if 'OIDC_CLIENT_SECRETS' in app.config.keys():
        oidc.init_app(app)
    else:
        app.logger.warning('Running without any authentication/authorisation')

    #
    # Import and register our APIs here

    from mrmat_python_api_flask.apis.healthz import api_healthz  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v1 import api_greeting_v1  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v2 import api_greeting_v2  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v3 import api_greeting_v3  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.resource.v1 import api_resource_v1  # pylint: disable=import-outside-toplevel
    api.register_blueprint(api_healthz, url_prefix='/healthz')
    api.register_blueprint(api_greeting_v1, url_prefix='/api/greeting/v1')
    api.register_blueprint(api_greeting_v2, url_prefix='/api/greeting/v2')
    api.register_blueprint(api_greeting_v3, url_prefix='/api/greeting/v3')
    api.register_blueprint(api_resource_v1, url_prefix='/api/resource/v1')

    #
    # If OAuth2 is in use, register our usage

    api.spec.components.security_scheme('mrmat_keycloak', {
        'type': 'oauth2',
        'flows': {
            'authorizationCode': {
                'authorizationUrl': 'https://keycloak.mrmat.org/auth/realms/master/protocol/openid-connect/auth',
                'tokenUrl': 'https://keycloak.mrmat.org/auth/realms/master/protocol/openid-connect/token',
                'scopes': {
                    'openid': 'Basic token without extra authorisation',
                    'mrmat-python-api-flask-resource-read': 'Allows reading objects '
                                                            'in the Resource API',
                    'mrmat-python-api-flask-resource-write': 'Allows creating/modifying'
                                                             ' and deleting objects '
                                                             'in the Resource API'
                }
            }
        }})
    # api.spec.components.security_scheme('mrmat_keycloak', {
    #     'type': 'openIdConnect',
    #     'openIdConnectUrl': 'https://keycloak.mrmat.org/auth/realms/master/.well-known/openid-configuration'
    # })
    # api.spec.security('mrmat_keycloak', [
    #     'profile',
    #     'mrmat-python-api-flask-resource-write',
    #     'mrmat-python-api-flask-resource-read'
    # ])

    @app.route('/apidoc/swagger/oauth2-redirect')
    def oauth2_redirect():
        return render_template('swagger-ui-redirect.html')
        # state = request.args.get('state')
        # code = request.args.get('code')
        # session_state = request.args.get('session_state')
        # return {'state': state, 'code': code, 'session_state': session_state}, 200


    return app
