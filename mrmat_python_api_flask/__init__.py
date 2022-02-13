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
import logging
import logging.config
import secrets
import importlib.metadata

import flask
from flask import Flask, has_request_context, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect

#
# Establish consistent logging
# The logger we obtain here is an operational logger, not the one logging requests. The former uses the matching
# logger '__name__', the latter uses 'werkzeug'


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.blueprint = request.blueprint
            record.url = request.full_path
            record.remote_addr = request.remote_addr
            record.user_agent = request.user_agent
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)


logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(name)-22s %(levelname)-8s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default'
            }
        },
        'loggers': {
            __name__: {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'formatter': 'default',
            'handlers': ['console']
        }
    })
log = logging.getLogger(__name__)

#
# Establish consistent logging

#
# Determine the version we're at and a version header we add to each response

try:
    __version__ = importlib.metadata.version('mrmat-python-api-flask')
except importlib.metadata.PackageNotFoundError:
    # You have not actually installed the wheel yet. We may be within CI so pick that version or fall back
    __version__ = os.environ.get('MRMAT_VERSION', '0.0.0.dev0')

#
# Initialise supporting services

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
oidc = OpenIDConnect()


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
    app_config_file = os.path.expanduser(os.environ.get('APP_CONFIG', '~/etc/mrmat-python-api-flask.json'))
    if os.path.exists(app_config_file):
        log.info(f'Applying configuration from {app_config_file}')
        app.config.from_json(app_config_file)
    if config_override is not None:
        for override in config_override:
            log.info(f'Overriding configuration for {override} from the command line')
        app.config.from_mapping(config_override)
    if app.config['SECRET_KEY'] is None:
        log.warning('Generating new secret key')
        app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

    #
    # Create the instance folder if it does not exist

    try:
        if not os.path.exists(app.instance_path):
            log.info(f'Creating new instance path at {app.instance_path}')
            os.makedirs(app.instance_path)
        else:
            log.info(f'Using existing instance path at {app.instance_path}')
    except OSError:
        log.error(f'Failed to create new instance path at {app.instance_path}')
        sys.exit(1)

    # When using Flask-SQLAlchemy, there is no need to explicitly import DAO classes because they themselves
    # inherit from the SQLAlchemy model

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    if 'OIDC_CLIENT_SECRETS' in app.config.keys():
        oidc.init_app(app)
    else:
        log.warning('Running without any authentication/authorisation')

    #
    # Import and register our APIs here

    from mrmat_python_api_flask.apis.healthz import api_healthz          # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v1 import api_greeting_v1  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v2 import api_greeting_v2  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.greeting.v3 import api_greeting_v3  # pylint: disable=import-outside-toplevel
    from mrmat_python_api_flask.apis.resource.v1 import api_resource_v1  # pylint: disable=import-outside-toplevel
    app.register_blueprint(api_healthz, url_prefix='/healthz')
    app.register_blueprint(api_greeting_v1, url_prefix='/api/greeting/v1')
    app.register_blueprint(api_greeting_v2, url_prefix='/api/greeting/v2')
    app.register_blueprint(api_greeting_v3, url_prefix='/api/greeting/v3')
    app.register_blueprint(api_resource_v1, url_prefix='/api/resource/v1')

    #
    # Postprocess the request
    # Log its result and add our version header to it

    @app.after_request
    def after_request(response: flask.Response) -> flask.Response:
        log.info(f'[{response.status_code}]')
        response.headers.add('X-MrMat-Python-API-Flask-Version', __version__)
        return response

    return app
