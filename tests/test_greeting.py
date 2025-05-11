#  MIT License
#
#  Copyright (c) 2025 Mathieu Imfeld
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

import pytest
import flask.testing

from mrmat_python_api_flask.apis.greeting.v1 import GreetingV1, greeting_v1_schema
from mrmat_python_api_flask.apis.greeting.v2 import (
    GreetingV2, greeting_v2_schema,
)

def test_greeting_v1(client: flask.testing.Client):
    response = client.get("/api/greeting/v1/")
    assert response.status_code == 200
    greeting = greeting_v1_schema.load(response.json)
    assert isinstance(greeting, GreetingV1)
    assert greeting.message == 'Hello World'

def test_greeting_v2(client: flask.testing.Client):
    response = client.get("/api/greeting/v2/")
    assert response.status_code == 200
    greeting = greeting_v2_schema.load(response.json)
    assert isinstance(greeting, GreetingV2)
    assert greeting.message == 'Hello Stranger'

@pytest.mark.parametrize('name', ['MrMat', 'Chris', 'Michal', 'Alexandre', 'Jerome'])
def test_greeting_v2_custom(client: flask.testing.Client, name: str):
    response = client.get("/api/greeting/v2/", query_string={'name': name})
    assert response.status_code == 200
    greeting = greeting_v2_schema.load(response.json)
    assert isinstance(greeting, GreetingV2)
    assert greeting.message == f'Hello {name}'
