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

import pytest
from datetime import datetime

from resource_api_client import ResourceAPIClient


@pytest.mark.usefixtures('local_test_infrastructure')
class TestWithLocalInfrastructure:

    def test_resource_lifecycle(self, tmpdir, local_test_infrastructure):
        with local_test_infrastructure.app_client(tmpdir) as client:
            with local_test_infrastructure.user_token(scopes=['mpaf-read', 'mpaf-write']) as user_token:
                rac = ResourceAPIClient(client, token=user_token['access_token'])

                resource_name = f'Test Resource {datetime.utcnow()}'
                (resp, resp_body) = rac.create(name=resource_name)
                assert resp.status_code == 201
                assert resp_body['id'] is not None
                assert resp_body['name'] == resource_name
                resource_id = resp_body['id']

                (resp, resp_body) = rac.get_all()
                assert resp.status_code == 200
                assert 'resources' in resp_body
                assert len(resp_body['resources']) == 0

                (resp, resp_body) = rac.get_one(resource_id)
                assert resp.status_code == 200
                assert resp_body['id'] == resource_id
                assert resp_body['name'] == resource_name

                resource_name_modified = f'Modified Resource {datetime.utcnow()}'
                (resp, resp_body) = rac.modify(resource_id, name=resource_name_modified)
                assert resp.status_code == 200
                assert resp_body['id'] == resource_id
                assert resp_body['name'] == resource_name_modified

                (resp, resp_body) = rac.remove(resource_id)
                assert resp.status_code == 204
                assert resp_body is None

                (resp, resp_body) = rac.remove(resource_id)
                assert resp.status_code == 410
                assert resp_body['message'] == 'The requested resource is permanently deleted'
                assert resp_body['status'] == 410

    def test_insufficient_scope(self, tmpdir, local_test_infrastructure):
        with local_test_infrastructure.app_client(tmpdir) as client:
            with local_test_infrastructure.user_token(scopes=['mpaf-read']) as user_token:
                rac = ResourceAPIClient(client, token=user_token['access_token'])

                (resp, resp_body) = rac.create(name='Unauthorised')
                assert resp.status_code == 401
                assert resp_body is None

                (resp, resp_body) = rac.modify(1, name='Unauthorised')
                assert resp.status_code == 401

                (resp, resp_body) = rac.remove(1)
                assert resp.status_code == 401
                assert resp_body is None
