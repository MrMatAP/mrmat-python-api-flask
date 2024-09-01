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
import json
import logging.config
import secrets
import importlib.metadata

import flask
from flask import Flask, has_request_context, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_smorest import Api
from authlib.integrations.flask_client import OAuth

#
# Establish consistent logging

#
# Determine the version we're at and a version header we add to each response

try:
    __version__ = importlib.metadata.version('mrmat-python-api-flask')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'
__app_version_header__ = 'X-MrMat-Python-API-Flask-Version'

#
# Initialize supporting services

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
api = Api()
oauth = OAuth()


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
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)

    #
    # Set configuration defaults. If a config file is present then load it. If we have overrides, apply them

    app.config.setdefault('SQLALCHEMY_DATABASE_URI',
                          'sqlite+pysqlite:///' + os.path.join(app.instance_path, 'mrmat-python-api-flask.sqlite'))
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('OIDC_USER_INFO_ENABLED', True)
    app.config.setdefault('OIDC_RESOURCE_SERVER_ONLY', True)
    app.config.setdefault('API_TITLE', 'MrMat :: Python :: API :: Flask')
    app.config.setdefault('API_VERSION', __version__)
    app.config.setdefault('OPENAPI_VERSION', '3.0.2')
    app.config.setdefault('OPENAPI_URL_PREFIX', '/doc')
    app.config.setdefault('OPENAPI_JSON_PATH', '/openapi.json')
    app.config.setdefault('OPENAPI_SWAGGER_UI_PATH', '/swagger-ui')
    app.config.setdefault('OPENAPI_SWAGGER_UI_URL', 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.5.0/')
    app_config_file = os.environ.get('APP_CONFIG', os.path.expanduser('~/etc/mrmat-python-api-flask.json'))
    if os.path.exists(app_config_file):
        app.logger.info('Applying configuration from %s', app_config_file)
        with open(app_config_file, 'r', encoding='UTF-8') as c:
            config = json.load(c)
            app.config.from_object(config)
    if config_override is not None:
        for override in config_override:
            app.logger.info('Overriding configuration for %s from the command line', override)
        app.config.from_mapping(config_override)
    if app.config['SECRET_KEY'] is None:
        app.logger.warning('Generating new secret key')
        app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

    #
    # Create the instance folder if it does not exist

    try:
        if not os.path.exists(app.instance_path):
            app.logger.info('Creating new instance path at %s', app.instance_path)
            os.makedirs(app.instance_path)
        else:
            app.logger.info('Using existing instance path at %s', app.instance_path)
    except OSError:
        app.logger.error('Failed to create new instance path at %s', app.instance_path)
        sys.exit(1)

    # There is no need to explicitly load DAO classes here because they inherit from the SQLAlchemy model

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    api.init_app(app)
    oauth.init_app(app)
    oauth.register(name='mrmat',
                   server_metadata_url='http://localhost:5001/.well-known/openid-configuration',
                   client_kwargs={'scope':'openid email profile'})
    # if 'OIDC_CLIENT_SECRETS' in app.config.keys():
    #     oauth.init_app(app)
    #     oauth.register(name='mrmat',
    #                    server_metadata_url='http://localhost:5001/.well-known/openid-configuration',
    #                    client_kwargs={'scope':'openid email profile'})
    # else:
    #     app.logger.warning('Running without any authentication/authorisation')

    #
    # Set Security Schemes in the generated OpenAPI descriptor

    # api.spec.components.security_scheme('openId',
    #                                     {'type': 'openIdConnect',
    #                                      'description': 'MrMat OIDC',
    #                                      'openIdConnectUrl': 'http://localhost:8080/auth/realms/master/.well-known'
    #                                                          '/openid-configuration'})

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
    # Postprocess the request
    # Log its result and add our version header to it

    @app.after_request
    def after_request(response: flask.Response) -> flask.Response:
        app.logger.info('[%s]', response.status_code)
        response.headers.add(__app_version_header__, __version__)
        return response

    return app
