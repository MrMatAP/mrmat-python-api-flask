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
Tests for the Greeting V3 API
"""

import pytest
import requests
import flask.testing

from mrmat_python_api_flask.apis.greeting.v3 import GreetingV3, greeting_v3_output_schema


@pytest.mark.usefixtures('mock_idp', 'local_app_client', 'auth_app_client')
class TestGreetingV3:
    """
    Test the GreetingV3 API
    """

    def test_mock_idp(self, mock_idp, local_app_client):
        idp_discovery = requests.get('http://localhost:5001/.well-known/openid-configuration').json()
        idp_keys = requests.get('http://localhost:5001/keys').json()
        idp_token = requests.get('http://localhost:5001/connect/authorization').text
        idp_register_api = requests.post('http://localhost:5001/connect/register', json={
            'client_name': 'mrmat-python-api-flask',
            'redirect_uris': ['http://localhost:5000']
        }).json()
        requests.post('http://localhost:5001/connect/register', json={
            'client_name': 'mrmat-python-api-client',
            'redirect_uris': ['http://localhost:5000']
        }).json()
        idp_authorization = requests.post()
        pass

    def test_greeting_v3(self, mock_idp, auth_app_client):
        user = mock_idp.register_user(given_name='Mathieu',
                                      family_name='Imfeld',
                                      email='foo@bar.com',
                                      name='Mathieu Imfeld',
                                      sub='imfeldma')
        clients = list(mock_idp.clients.keys())
        user_token = mock_idp.token(clients[0], user.sub)

        response: flask.testing.TestResponse = auth_app_client.get('/api/greeting/v3/', headers={
            'Authorization': f'Bearer {user_token.get("id_token")}'
        })
        assert response.status_code == 200, 'We get a success response'
        assert response.content_type == 'application/json', 'The content type is JSON'
        body = greeting_v3_output_schema.load(response.json)
        assert isinstance(body, GreetingV3), 'The response body is a GreetingV1 object'
        assert body.message == 'Hello Stranger', 'The GreetingV3 object contains the expected greeting'
