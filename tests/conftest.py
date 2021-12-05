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
from typing import Optional, List, Dict

import pytest
import requests
import oauthlib.oauth2
import requests_oauthlib

import jwt
import contextlib
import secrets
import psycopg2
import psycopg2.sql
import psycopg2.extensions

from flask_migrate import upgrade
from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakOperationError

from mrmat_python_api_flask import create_app, db

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

    _db_admin_conn: psycopg2.extensions.connection = None
    _auth_admin_token: str = None

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
            self._db_admin_conn = psycopg2.connect(self.config['db']['admin_dsn'])
        if 'auth' in self.config:
            self._keycloak_admin = KeycloakAdmin(server_url=self.config['auth']['admin_url'],
                                                 username=self.config['auth']['admin_user'],
                                                 password=self.config['auth']['admin_password'],
                                                 realm_name=self.config['auth']['admin_realm'],
                                                 verify=True)

    def teardown(self):
        if self._db_admin_conn is not None:
            self._db_admin_conn.close()

    @contextlib.contextmanager
    def db_dsn(self,
               role: str = 'test',
               password: str = 'test',
               schema: str = 'test',
               drop_finally: bool = False):
        with self._db_admin_conn.cursor() as cur:
            cur.execute("SELECT COUNT(rolname) FROM pg_roles WHERE rolname = %(role_name)s;",
                        {'role_name': role})
            role_count = cur.fetchone()
            if role_count[0] == 0:
                cur.execute(
                    psycopg2.sql.SQL('CREATE ROLE {} ENCRYPTED PASSWORD %(password)s LOGIN').format(
                        psycopg2.sql.Identifier(role)),
                    {'password': password})
                self._db_admin_conn.commit()
            cur.execute(psycopg2.sql.SQL('CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}').format(
                psycopg2.sql.Identifier(schema),
                psycopg2.sql.Identifier(role)))
            self._db_admin_conn.commit()
            cur.execute(psycopg2.sql.SQL('ALTER ROLE {} SET search_path TO {}').format(
                psycopg2.sql.Identifier(role),
                psycopg2.sql.Identifier(schema)))
            self._db_admin_conn.commit()
        try:
            dsn_info = psycopg2.extensions.ConnectionInfo = psycopg2.extensions.parse_dsn(self.admin_dsn)
            user_dsn = f"postgresql://{role}:{password}@{dsn_info['host']}:{dsn_info['port']}/{dsn_info['dbname']}"
            yield user_dsn
        finally:
            if drop_finally:
                LOGGER.info(f'Dropping schema {schema} and associated role {role}')
                with self._db_admin_conn.cursor() as cur:
                    cur.execute(
                        psycopg2.sql.SQL('DROP SCHEMA {} CASCADE').format(
                            psycopg2.sql.Identifier(schema)))
                    cur.execute(
                        psycopg2.sql.SQL('DROP ROLE {}').format(
                            psycopg2.sql.Identifier(role)))
                    self._db_admin_conn.commit()

    @contextlib.contextmanager
    def auth_user(self,
                  tmpdir,
                  client_id: str = 'test-client',
                  ted_id: str = 'ted-client',
                  user_id: str = 'test-user',
                  user_password: str = 'test-password',
                  scopes: List[str] = None,
                  scope: str = 'test-scope',
                  redirect_uris: List = None,
                  drop_finally: bool = False):
        try:
            if scopes is None:
                scopes = []
            for scope in scopes:
                self._keycloak_admin.create_client_scope({
                    'id': scope,
                    'name': scope,
                    'description': f'Test {scope}',
                    'protocol': 'openid-connect'
                }, skip_exists=True)
            if not self._keycloak_admin.get_client_id(client_id):
                self._keycloak_admin.create_client({
                    'id': client_id,
                    'name': client_id,
                    'publicClient': False,
                    'optionalClientScopes': scopes
                })
            client_secret = self._keycloak_admin.generate_client_secrets(client_id)
            if not self._keycloak_admin.get_client_id(ted_id):
                self._keycloak_admin.create_client({
                    'id': ted_id,
                    'name': ted_id,
                    'publicClient': False,
                    'redirectUris': ['http://localhost'],
                    'directAccessGrantsEnabled': True,
                    'optionalClientScopes': scopes
                })
            ted_secret = self._keycloak_admin.generate_client_secrets(ted_id)

            self._keycloak_admin.create_user({
                'id': user_id,
                'emailVerified': True,
                'enabled': True,
                'firstName': 'Test',
                'lastName': 'User',
                'username': user_id,
                'credentials': [
                    {'value': user_password}
                ]
            }, exist_ok=True)

            keycloak = KeycloakOpenID(server_url=self._keycloak_admin.server_url,
                                      client_id=ted_id,
                                      client_secret_key=ted_secret['value'],
                                      realm_name='master',
                                      verify=True)
            discovery = keycloak.well_know()
            with open(f'{tmpdir}/client_secrets.json', 'w') as cs:
                json.dump({
                    'web': {
                        'client_id': client_id,
                        'client_secret': client_secret['value'],
                        'auth_uri': discovery['authorization_endpoint'],
                        'token_uri': discovery['token_endpoint'],
                        'userinfo_uri': discovery['userinfo_endpoint'],
                        'token_introspection_uri': discovery['introspection_endpoint'],
                        'issuer': discovery['issuer'],
                        'redirect_uris': redirect_uris
                    }
                }, cs)

            self._auth_info = {
                'client_secrets_file': f'{tmpdir}/client_secrets.json',
                'client_id': client_id,
                'client_secret': client_secret['value'],
                'ted_id': ted_id,
                'ted_secret': ted_secret['value'],
                'user_id': user_id,
                'user_password': user_password,
                'scope': scope
            }
            yield self._auth_info

        except KeycloakOperationError as koe:
            LOGGER.exception(koe)
        finally:
            if drop_finally:
                LOGGER.info(f'Deleting user_id {user_id}')
                self._keycloak_admin.delete_user(user_id)
                LOGGER.info(f'Deleting client_id {client_id}')
                self._keycloak_admin.delete_client(client_id)
                LOGGER.info(f'Deleting client_id {ted_id}')
                self._keycloak_admin.delete_client(ted_id)
                LOGGER.info(f'Deleting scope {scope}')

    @contextlib.contextmanager
    def auth_token(self, scopes: List[str]):
        try:
            keycloak = KeycloakOpenID(server_url=self._keycloak_admin.server_url,
                                      client_id=self._auth_info['ted_id'],
                                      client_secret_key=self._auth_info['ted_secret'],
                                      realm_name='master',
                                      verify=True)
            token = keycloak.token(self._auth_info['user_id'],
                                   self._auth_info['user_password'],
                                   scope=scopes)
            yield token
        finally:
            pass


@pytest.fixture(scope='session', autouse=False)
def ted() -> TED:
    """
    Main fixture for Test Environment on Demand

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


@pytest.fixture
def ted_client(ted, tmpdir):
    with ted.db_dsn(role='mpaf', password='mpaf', schema='mpaf') as dsn:
        with ted.auth_user(tmpdir, scopes=['mpaf-read', 'mpaf-write']) as auth:
            app = create_app({
                'TESTING': True,
                'SECRET_KEY': secrets.token_hex(16),
                'SQLALCHEMY_DATABASE_URI': dsn,
                'OIDC_CLIENT_SECRETS': auth['client_secrets_file']
            })
            with app.app_context():
                upgrade(directory=os.path.join(os.path.dirname(__file__), '..', 'migrations'))
                db.create_all()
            with app.test_client() as client:
                yield {'auth': auth, 'client': client}
