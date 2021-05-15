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
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import sys
import os
import pkg_resources
from logging.config import dictConfig

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect


__version__ = pkg_resources.get_distribution('mrmat-python-api-flask').version
db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
oidc = OpenIDConnect()

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
    """
    Factory method to create a Flask app.

    Allows configuration overrides by providing the optional test_config dict as well as a `config.py`
    within the instance_path. Will create the instance_path if it does not exist. instance_path is meant
    to be outside the package directory.

    Args:
        config_override: Optional dict to override configuration
        instance_path: Optional fully qualified path to instance directory (for configuration etc)

    Returns: an initialised Flask app object

    """
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    app.config.from_mapping(
        SECRET_KEY=os.urandom(16),
        SQLALCHEMY_DATABASE_URI='sqlite+pysqlite:///' + os.path.join(app.instance_path,
                                                                     'mrmat-python-api-flask.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        OIDC_RESOURCE_SERVER_ONLY=True)
    if config_override is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(config_override)
    try:
        if not os.path.exists(app.instance_path):
            app.logger.info(f'Creating new instance path at {app.instance_path}')
            os.makedirs(app.instance_path)
        else:
            app.logger.info(f'Using instance path at {app.instance_path}')
    except OSError:
        app.logger.error(f'Failed to create instance path at {app.instance_path}')
        sys.exit(1)

    # TODO: When using Flask-SQLAlchemy, the following import is not required because we're importing db.Model in the
    #       SQLAlchemy classes
    # from .dao.resource import ResourceDAO
    global db, ma, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    oidc.init_app(app)

    #
    # Import our APIs here

    from mrmat_python_api_flask.apis.healthz import bp as api_healthz
    from mrmat_python_api_flask.apis.greeting.v1 import api_greeting_v1
    from mrmat_python_api_flask.apis.greeting.v2 import api_greeting_v2
    from mrmat_python_api_flask.apis.resource.v1 import api_resource_v1
    app.register_blueprint(api_healthz, url_prefix='/healthz')
    app.register_blueprint(api_greeting_v1, url_prefix='/api/greeting/v1')
    app.register_blueprint(api_greeting_v2, url_prefix='/api/greeting/v2')
    app.register_blueprint(api_resource_v1, url_prefix='/api/resource/v1')

    return app
