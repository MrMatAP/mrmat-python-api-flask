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

"""
Code available to the entire testsuite
"""

import os
import logging
import json
import pathlib
import contextlib
import abc
from typing import Optional, List, Dict

import pytest

import secrets
import psycopg2
import psycopg2.sql
import psycopg2.extensions

from flask_migrate import upgrade
from keycloak.keycloak_admin import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakOperationError

from mrmat_python_api_flask import create_app, db

LOGGER = logging.getLogger(__name__)


class TIException(Exception):
    """
    An dedicated exception raised when issues occur establishing the test infrastructure
    """
    skip: bool = False
    msg: str = 'An unexpected exception occurred'

    def __init__(self, msg: str, skip: Optional[bool] = False):
        super().__init__()
        self.skip = skip
        self.msg = msg


class AbstractTestInfrastructure(abc.ABC):
    """
    An abstract class dedicated to any local test infrastructure implementation
    """

    _app = None

    @abc.abstractmethod
    def app(self):
        pass

    @abc.abstractmethod
    def app_client(self):
        pass


class NoTestInfrastructure(AbstractTestInfrastructure):
    """
    An implementation of test infrastructure that does not rely on anything (e.g. there is nothing
    available except what we have right here)
    """

    @contextlib.contextmanager
    def app(self):
        self._app = create_app({
            'TESTING': True,
            'SECRET_KEY': secrets.token_hex(16)
        })
        with self._app.app_context():
            upgrade(directory=os.path.join(os.path.dirname(__file__), '..', 'migrations'))
            db.create_all()
        yield self._app

    @contextlib.contextmanager
    def app_client(self):
        with self.app() as app:
            yield app.test_client()


class LocalTestInfrastructure(object):
    """
    A class for administration of the available local test infrastructure
    """

    _ti_config_path: pathlib.Path = None
    _ti_config: Dict = {}

    _pg_admin = None
    _keycloak_admin: KeycloakAdmin
    _auth_info: Dict = {}
    _app = None

    def __init__(self, ti_config_path: pathlib.Path):
        if not ti_config_path.exists():
            raise TIException(skip=True, msg=f'Configuration at {ti_config_path} is not readable or does not exist')
        self._ti_config_path = ti_config_path
        self._ti_config = json.loads(self._ti_config_path.read_text(encoding='UTF-8'))
        if 'pg' not in self._ti_config or 'keycloak' not in self._ti_config:
            raise TIException(skip=True, msg='Missing configuration for local test infrastructure')
        try:
            self._pg_admin = psycopg2.connect(self._ti_config['pg'].get('admin_dsn'))
            self._keycloak_admin = KeycloakAdmin(server_url=self._ti_config['keycloak'].get('admin_url'),
                                                 username=self._ti_config['keycloak'].get('admin_user'),
                                                 password=self._ti_config['keycloak'].get('admin_password'),
                                                 realm_name='master')
        except psycopg2.OperationalError as oe:
            raise TIException(skip=True, msg='Failed to obtain an administrative connection to PG') from oe
        except KeycloakOperationError as koe:
            raise TIException(skip=True, msg='Failed to obtain an administrative connection to KeyCloak') from koe

    @contextlib.contextmanager
    def app_dsn(self,
                role: str = 'test',
                password: str = 'test',
                schema: str = 'test',
                drop_finally: bool = False):
        try:
            cur = self._pg_admin.cursor()
            cur.execute('SELECT COUNT(rolname) FROM pg_roles WHERE rolname = %(role_name)s;', {'role_name': role})
            role_count = cur.fetchone()
            if role_count[0] == 0:
                cur.execute(
                    psycopg2.sql.SQL('CREATE ROLE {} ENCRYPTED PASSWORD %(password)s LOGIN').format(
                        psycopg2.sql.Identifier(role)),
                    {'password': password})
            cur.execute(psycopg2.sql.SQL('CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}').format(
                psycopg2.sql.Identifier(schema),
                psycopg2.sql.Identifier(role)))
            cur.execute(psycopg2.sql.SQL('ALTER ROLE {} SET search_path TO {}').format(
                psycopg2.sql.Identifier(role),
                psycopg2.sql.Identifier(schema)))
            self._pg_admin.commit()
            cur.close()

            dsn_info = psycopg2.extensions.ConnectionInfo = psycopg2.extensions.parse_dsn(self._ti_config['pg'].
                                                                                          get('admin_dsn'))
            app_dsn = f"postgresql://{role}:{password}@{dsn_info['host']}:{dsn_info['port']}/{dsn_info['dbname']}"
            yield app_dsn

        except psycopg2.Error as e:
            raise TIException(msg=f'Failed to create role {role} on schema {schema}') from e
        finally:
            if drop_finally:
                LOGGER.info('Dropping schema %s and associated role %s', schema, role)
                cur = self._pg_admin.cursor()
                cur.execute(
                    psycopg2.sql.SQL('DROP SCHEMA {} CASCADE').format(psycopg2.sql.Identifier(schema)))
                cur.execute(
                    psycopg2.sql.SQL('DROP ROLE {}').format(psycopg2.sql.Identifier(role)))
                self._pg_admin.commit()
                cur.close()

    @contextlib.contextmanager
    def app_auth(self,
                 tmpdir,
                 client_id: str = 'test-client',
                 ti_id: str = 'ti-client',
                 scopes: List[str] = None,
                 redirect_uris: List = None,
                 drop_finally: bool = False):
        try:
            if scopes is None:
                scopes = []
            for s in scopes:
                if not self._keycloak_admin.get_client_scope(s):
                    self._keycloak_admin.create_client_scope({
                        'id': s,
                        'name': s,
                        'description': f'Test {s}',
                        'protocol': 'openid-connect'
                    })
            if not self._keycloak_admin.get_client_id(client_id):
                self._keycloak_admin.create_client({
                    'id': client_id,
                    'name': client_id,
                    'publicClient': False,
                    'optionalClientScopes': scopes
                })
            client_secret = self._keycloak_admin.generate_client_secrets(client_id)
            if not self._keycloak_admin.get_client_id(ti_id):
                self._keycloak_admin.create_client({
                    'id': ti_id,
                    'name': ti_id,
                    'publicClient': False,
                    'redirectUris': ['http://localhost'],
                    'directAccessGrantsEnabled': True,
                    'optionalClientScopes': scopes
                })
            ted_secret = self._keycloak_admin.generate_client_secrets(ti_id)

            keycloak = KeycloakOpenID(server_url=self._keycloak_admin.server_url,
                                      client_id=ti_id,
                                      client_secret_key=ted_secret['value'],
                                      realm_name='master',
                                      verify=True)
            discovery = keycloak.well_know()
            with open(f'{tmpdir}/client_secrets.json', 'w', encoding='UTF-8') as cs:
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
                'ti_id': ti_id,
                'ti_secret': ted_secret['value']
            }
            yield self._auth_info

        except KeycloakOperationError as koe:
            LOGGER.exception(koe)
        finally:
            if drop_finally:
                LOGGER.info('Deleting client_id %s', client_id)
                self._keycloak_admin.delete_client(client_id)
                LOGGER.info('Deleting client_id %s', ti_id)
                self._keycloak_admin.delete_client(ti_id)

    @contextlib.contextmanager
    def app(self,
            tmpdir,
            pg_role: str = 'mpaf-test',
            pg_password: str = 'mpaf-test',
            pg_schema: str = 'mpaf-test',
            drop_finally: bool = False):
        with self.app_dsn(role=pg_role, password=pg_password, schema=pg_schema, drop_finally=drop_finally) as dsn, \
                self.app_auth(tmpdir, scopes=['mpaf-read', 'mpaf-write']) as auth:
            self._app = create_app({
                'TESTING': True,
                'SECRET_KEY': secrets.token_hex(16),
                'SQLALCHEMY_DATABASE_URI': dsn,
                'OIDC_CLIENT_SECRETS': auth['client_secrets_file']
            })
            with self._app.app_context():
                upgrade(directory=os.path.join(os.path.dirname(__file__), '..', 'migrations'))
                db.create_all()
            yield self._app

    @contextlib.contextmanager
    def app_client(self, app_dir):
        with self.app(app_dir) as app:
            yield app.test_client()

    @contextlib.contextmanager
    def user_token(self,
                   user_id: str = 'mpaf-test-user',
                   user_password: str = 'mpaf-test-user',
                   scopes: List[str] = None,
                   drop_finally: bool = False):
        try:
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
                                      client_id=self._auth_info['ti_id'],
                                      client_secret_key=self._auth_info['ti_secret'],
                                      realm_name='master',
                                      verify=True)
            token = keycloak.token(user_id, user_password, scope=scopes)
            token['user_id'] = user_id
            yield token
        finally:
            if drop_finally:
                LOGGER.info('Deleting user %s', user_id)
                self._keycloak_admin.delete_user(user_id)


@pytest.fixture(scope='module', autouse=False, )
def no_test_infrastructure():
    """
    Class-wide fixture for when no test infrastructure is available
    Yields: An initialised NoTestInfrastructure object
    """
    yield NoTestInfrastructure()


@pytest.fixture(scope='class', autouse=False)
def local_test_infrastructure():
    """
    Class-wide fixture to read the configuration of locally available test infrastructure from the `TI_CONFIG`
    environment variable.

    Yields: An initialised TI object

    """
    if 'TI_CONFIG' not in os.environ:
        pytest.skip('There is TI_CONFIG environment variable configuring local infrastructure to test with')
    yield LocalTestInfrastructure(ti_config_path=pathlib.Path(os.path.expanduser(os.getenv('TI_CONFIG'))))
