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

import os
import logging
import json

import psycopg2
import psycopg2.sql
import psycopg2.extensions
import pytest

from typing import Optional, List, Dict

import jwt
import oauthlib.oauth2
import requests_oauthlib
from flask_migrate import upgrade

from mrmat_python_api_flask import create_app, db, migrate

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def test_config() -> Optional[Dict]:
    """Read the test configuration file the FLASK_CONFIG environment variable points to

    A token can only be obtained if the configuration file pointed to by the FLASK_CONFIG environment variable
    contains required entries to set up OIDC for testing. An empty dict is returned if these are not present.
    The following are required:

    {
        "web": {                This entry is required to be the very first entry. If you don't like that,
                                then externalize it into a separate file and point to it via OIDC_CLIENT_SECRETS
            "client_id":        Server side client_id
            "client_secret":    Server-side client_secret
            ...
        },
        "client": {
            "client_id":        Test client client_id
            "client_secret":    Test client secret
            "preferred_name":   Asserted preferred_name of the client_id
        "OIDC_CLIENT_SECRETS":  Point this to the same place as FLASK_CONFIG (to reduce the number of config files
    Returns:
        A dictionary of configuration or None if not configuration file is set
    """
    config_file = os.path.expanduser(os.getenv('FLASK_CONFIG'))
    if not os.path.exists(config_file):
        LOGGER.info('Configuration set via FLASK_CONFIG environment variable does not exist. Tests are limited')
        return None
    with open(os.path.expanduser(os.environ['FLASK_CONFIG'])) as C:
        return json.load(C)


@pytest.fixture
def client():
    """Start and configure the WSGI app.

    Configuration honours the FLASK_CONFIG environment variable but will set reasonable defaults if not present. This
    particularly overrides the configuration of an in-memory database rather than the normal persisted database in the
    instance directory.

    Yields:
        A Flask client used for testing
    """
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite://'})
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client


def oidc_token(config: Dict, scope: Optional[List]):
    """Obtain an OIDC token to be used for client testing.
    Args:
        config: Test configuration
        scope: Optional scope to request a token for. Defaults to ['openid']
    Returns:
        A dictionary containing the access token or None if configuration is lacking
    """
    if test_config is None or 'client' not in config:
        LOGGER.info('Missing OIDC test client configuration. Tests will be limited')
        return None
    for key in ['client_id', 'client_secret', 'preferred_name']:
        if key not in config['client']:
            LOGGER.info(f'Missing {key} in test client configuration. Tests will be limited')
            return None
    if scope is None:
        scope = ['openid']
    elif 'openid' not in scope:
        scope.insert(0, 'openid')
    client = oauthlib.oauth2.BackendApplicationClient(client_id=config['client']['client_id'], scope=scope)
    oauth = requests_oauthlib.OAuth2Session(client=client)
    return oauth.fetch_token(token_url=config['web']['token_uri'],
                             client_id=config['client']['client_id'],
                             client_secret=config['client']['client_secret'])


@pytest.fixture
def oidc_token_read(test_config) -> Optional[Dict]:
    """ Return an OIDC token with scope 'mrmat-python-api-flask-resource-read'

    Args:
        test_config: The test configuration as per the test_config fixture

    Returns:
        A Dict containing the desired token structure
    """
    if test_config is None:
        LOGGER.info('Missing OIDC test client configuration. Tests will be limited')
        return None
    token = oidc_token(test_config, ['mrmat-python-api-flask-resource-read'])
    token['jwt'] = jwt.decode(token['access_token'], options={"verify_signature": False})
    return token


@pytest.fixture
def oidc_token_write(test_config) -> Optional[Dict]:
    """ Return an OIDC token with scope 'mrmat-python-api-flask-resource-write'

    Args:
        test_config: The test configuration as per the test_config fixture

    Returns:
        A Dict containing the desired token structure
    """
    if test_config is None:
        LOGGER.info('Missing OIDC test client configuration. Tests will be limited')
        return None
    token = oidc_token(test_config, ['mrmat-python-api-flask-resource-write'])
    token['jwt'] = jwt.decode(token['access_token'], options={"verify_signature": False})
    return token


class TEDException(Exception):
    skip: bool = False
    msg: str = 'An unexpected exception occurred'

    def __init__(self, msg: str, skip: Optional[bool] = False):
        self.skip = skip
        self.msg = msg


class TED:
    available: bool = False
    config_file: str = None
    config: dict = {}

    _admin_conn: psycopg2.extensions.connection = None

    def __init__(self):
        if 'TED_CONFIG' not in os.environ:
            raise TEDException(skip=True,
                               msg='There is no TED_CONFIG environment variable to configure the environment')
        self.config_file = os.path.expanduser(os.getenv('TED_CONFIG'))
        if not os.path.exists(self.config_file):
            raise TEDException(skip=True, msg='Configuration from TED_CONFIG environment variable is not readable or '
                                              'does not exist')
        with open(self.config_file) as C:
            self.config = json.load(C)
        if 'db' in self.config:
            self.admin_dsn = self.config['db']['admin_dsn']
            self.user_dsn = self.config['db']['user_dsn']
            self.assert_db()

    def teardown(self):
        if self._admin_conn is not None:
            self._admin_conn.close()

    def assert_db(self):
        user_dsn_info: psycopg2.extensions.ConnectionInfo = psycopg2.extensions.parse_dsn(self.user_dsn)
        role = user_dsn_info['user']
        password = user_dsn_info['password']
        schema = self.config['db']['user_force_schema'] if 'user_force_schema' in self.config['db'] else role
        self._admin_conn = psycopg2.connect(self.config['db']['admin_dsn'])
        with self._admin_conn.cursor() as cur:
            cur.execute("SELECT COUNT(rolname) FROM pg_roles WHERE rolname = %(role_name)s;",
                        {'role_name': role})
            role_count = cur.fetchone()
            if role_count[0] == 0:
                cur.execute(
                    psycopg2.sql.SQL('CREATE ROLE {} ENCRYPTED PASSWORD %(password)s LOGIN').format(
                        psycopg2.sql.Identifier(role)),
                    {'password': password})
                self._admin_conn.commit()
            cur.execute(psycopg2.sql.SQL('CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}').format(
                psycopg2.sql.Identifier(schema),
                psycopg2.sql.Identifier(role)))
            self._admin_conn.commit()
            cur.execute(psycopg2.sql.SQL('ALTER ROLE {} SET search_path TO {}').format(
                psycopg2.sql.Identifier(role),
                psycopg2.sql.Identifier(schema)))
            self._admin_conn.commit()


@pytest.fixture(scope='session', autouse=False)
def ted() -> TED:
    """Test Environment on Demand

    Read a config file to establish a class containing information about the test environment to be injected into
    all tests that require one.
    """
    try:
        ted = TED()
        yield ted
        LOGGER.info('Teardown')
    except TEDException as te:
        if te.skip:
            pytest.skip(msg=te.msg)


@pytest.fixture(scope='module')
def ted_client(ted):
    ted.assert_db()
    app = create_app({'TESTING': True,
                      'SQLALCHEMY_DATABASE_URI': ted.config['db']['user_dsn']})
    with app.app_context():
        upgrade(directory=os.path.join(os.path.dirname(__file__), '..', 'migrations'))
        db.create_all()
    with app.test_client() as client:
        yield client
