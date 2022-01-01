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
import secrets
import importlib.metadata

from rich.console import Console
from rich.logging import RichHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect

logging.basicConfig(level='INFO',
                    handlers=[RichHandler(rich_tracebacks=True,
                                          show_path=False,
                                          omit_repeated_times=False)])
log = logging.getLogger(__name__)
console = Console()

try:
    __version__ = importlib.metadata.version('mrmat-python-api-flask')
except importlib.metadata.PackageNotFoundError:
    # You have not actually installed the wheel yet. We may be within CI so pick that version or fall back
    __version__ = os.environ.get('MRMAT_VERSION', '0.0.0.dev0')

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
        app.logger.info(f'Applying configuration from {app_config_file}')
        app.config.from_json(app_config_file)
    if config_override is not None:
        app.logger.info(f'Overriding configuration from {type(config_override)}')
        app.config.from_mapping(config_override)
    if app.config['SECRET_KEY'] is None:
        app.logger.warning('Generating new secret key')
        app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

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

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    if 'OIDC_CLIENT_SECRETS' in app.config.keys():
        oidc.init_app(app)
    else:
        app.logger.warning('Running without any authentication/authorisation')

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

    return app
