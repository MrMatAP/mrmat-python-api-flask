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
Tests for the Greeting V2 API
"""

import pytest
import flask.testing

from mrmat_python_api_flask.apis.greeting.v2 import GreetingV2Output, greeting_v2_output_schema


@pytest.mark.usefixtures('local_app_client')
class TestGreetingV2:
    """
    Test the GreetingV2 API
    """

    def test_greeting_v2_default(self, local_app_client):
        response: flask.testing.TestResponse = local_app_client.get('/api/greeting/v2/')
        assert response.status_code == 200, 'We get a success response'
        assert response.content_type == 'application/json', 'The content type is JSON'
        body = greeting_v2_output_schema.load(response.json)
        assert isinstance(body, GreetingV2Output), 'The response body is a GreetingV2 object'
        assert body.message == 'Hello Stranger', 'The GreetingV2 object contains the expected greeting'

    def test_greeting_v2_with_name(self, local_app_client):
        response: flask.testing.TestResponse = local_app_client.get('/api/greeting/v2/?name=MrMat')
        assert response.status_code == 200, 'We get a success response'
        assert response.content_type == 'application/json', 'The content type is JSON'
        body = greeting_v2_output_schema.load(response.json)
        assert isinstance(body, GreetingV2Output), 'The response body is a GreetingV2 object'
        assert body.message == 'Hello MrMat', 'The GreetingV2 object contains the expected greeting'
