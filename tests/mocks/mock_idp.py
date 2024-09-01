#  MIT License
#
#  Copyright (c) 2023 MrMat
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

#  MIT License
#
#  Copyright (c) 2023 MrMat
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

# Inspired by https://gist.github.com/eruvanos/f6f62edb368a20aaa880e12976620db8 (MIT license)
# Spec for registration: https://openid.net/specs/openid-connect-registration-1_0.html

import dataclasses
import typing
from datetime import datetime, timezone
import threading
import uuid
import secrets
import flask
from werkzeug.serving import make_server
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt


@dataclasses.dataclass
class Client:
    client_name: str
    redirect_uris: typing.List[str]
    client_id: str
    client_secret: typing.Optional[str] = None
    client_secret_expires_at: typing.Optional[int] = 0


@dataclasses.dataclass
class User:
    given_name: str
    family_name: str
    email: str
    name: str
    sub: str


class MockIDP:

    def __init__(self, port=5001):
        super().__init__()
        self.port = port
        self.app = flask.Flask(__name__)
        self.url = f'http://localhost:{port}'
        self.server = make_server('localhost', self.port, self.app)
        self.thread = None
        self.app.add_url_rule('/.well-known/openid-configuration', view_func=self.openid_configuration,
                              methods=('GET',))
        self.app.add_url_rule('/connect/authorization', view_func=self.authorization, methods=('GET', 'POST'))
        self.app.add_url_rule('/connect/token', view_func=self.api_token, methods=('GET',))
        self.app.add_url_rule('/userinfo', view_func=self.userinfo)
        self.app.add_url_rule('/keys', view_func=self.keys)
        self.app.add_url_rule('/connect/register', view_func=self.api_register_client, methods=('POST',))

        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = 0
        self.private_key = self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())
        self.public_key = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo) \
            .decode(encoding='UTF-8') \
            .replace('-----BEGIN PUBLIC KEY-----', '') \
            .replace('-----END PUBLIC KEY-----', '') \
            .replace('\n', '')
        self.clients: typing.Dict[str, Client] = {}
        self.codes = {}
        self.users: typing.Dict[str, User] = {}

    def openid_configuration(self) -> dict:
        return dict(
            issuer=self.url,
            authorization_endpoint=f'{self.url}/connect/authorization',
            token_endpoint=f'{self.url}/connect/token',
            userinfo_endpoint=f'{self.url}/userinfo',
            jwks_uri=f'{self.url}/keys',
            registration_endpoint=f'{self.url}/connect/register',
            response_types_supported=['code', 'id_token', 'token id_token'],
            subject_types_supported=['public'],
            id_token_signing_alg_values_supported=['RS256']
        )

    def authorization(self) -> dict:
        auth_in = flask.request.json
        client_id = auth_in['client_id']
        redirect_uri = auth_in['redirect_uri']

        if client_id not in self.clients:
            flask.redirect(f'{redirect_uri}?error=invalid_request&error_description="No such client_id"', code=302)
        if 'openid' not in auth_in['scope']:
            flask.redirect(f'{redirect_uri}?error=invalid_request&error_description="Missing openid scope"', code=302)
        code = secrets.token_urlsafe
        self.codes[code] = client_id
        flask.redirect(f'{redirect_uri}?code={code}')

    def api_token(self) -> dict:
        token_in = flask.request.json
        grant_type = token_in['grant_type']
        code = token_in['code']
        redirect_uri = token_in['redirect_uri']

        if code not in self.codes:
            return {'error': 'No such code was previously issued'}
        client_id = self.codes[code]
        return self.token(client_id=client_id, sub='foo')

    def token(self, client_id: str, sub: str):
        if sub not in self.users:
            return {'error': 'No such user'}
        user = self.users[sub]
        return {
            'token_type': 'Bearer',
            'expires_in': 3600,
            'access_token': 'foo',
            'refresh_token': 'bar',
            'id_token': jwt.encode(
                {
                    'iss': self.url,
                    'exp': int(datetime.now(timezone.utc).timestamp()) + 3600,
                    'aud': f'api://{client_id}',
                    'email': user.email,
                    'family_name': user.family_name,
                    'given_name': user.given_name,
                    'name': user.name,
                    'sub': user.sub,
                },
                headers={'kid': str(self.kid)},
                key=self.private_key,
                algorithm='RS256')
        }

    def userinfo(self):
        return 'TODO'

    def keys(self):
        return dict(
            kty='RSA',
            use='sig',
            kid=self.kid,
            x5t=self.kid,
            n=self.key.private_numbers().public_numbers.n,
            e=self.key.private_numbers().public_numbers.e,
            x5c=[self.public_key]
        )

    def api_register_client(self):
        reg_in = flask.request.json
        client = self.register_client(client_name=reg_in['client_name'], redirect_uris=reg_in['client_uris'])
        return client.__dict__

    def register_client(self, client_name: str, redirect_uris: typing.List) -> Client:
        client = Client(client_name=client_name,
                        redirect_uris=redirect_uris,
                        client_id=uuid.uuid4(),
                        client_secret=secrets.token_urlsafe(16))
        self.clients[client.client_id] = client
        return client

    def register_user(self,
                      given_name: str,
                      family_name: str,
                      email: str,
                      name: str,
                      sub: str) -> User:
        self.users[sub] = User(given_name=given_name,
                               family_name=family_name,
                               email=email,
                               name=name,
                               sub=sub)
        return self.users[sub]

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()
