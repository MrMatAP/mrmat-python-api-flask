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

import flask.testing
from mrmat_python_api_flask.apis.healthz.api import (
    Healthz, healthz_schema,
    Liveness, liveness_schema,
    Readiness, readiness_schema,
)

def test_healthz(client: flask.testing.Client):
    response = client.get("/api/healthz/")
    assert response.status_code == 200
    healthz = healthz_schema.load(data=response.json)
    assert isinstance(healthz, Healthz)
    assert healthz.status == 'OK'

def test_liveness(client: flask.testing.Client):
    response = client.get("/api/healthz/liveness")
    assert response.status_code == 200
    liveness = liveness_schema.load(data=response.json)
    assert isinstance(liveness, Liveness)
    assert liveness.status == 'OK'

def test_readiness(client: flask.testing.Client):
    response = client.get("/api/healthz/readiness")
    assert response.status_code == 200
    readiness = readiness_schema.load(data=response.json)
    assert isinstance(readiness, Readiness)
    assert readiness.status == 'OK'
