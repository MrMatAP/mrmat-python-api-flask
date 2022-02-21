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
Tests for the Resource API
"""

import pytest
from datetime import datetime

from resource_api_client import ResourceAPIClient


@pytest.mark.usefixtures('local_test_infrastructure')
class TestWithLocalInfrastructure:
    """
    Tests for the Resource API using locally available infrastructure
    """

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
                assert resp_body['code'] == 410
                assert resp_body['message'] == 'The requested resource is permanently deleted'

    def test_insufficient_scope(self, tmpdir, local_test_infrastructure):
        with local_test_infrastructure.app_client(tmpdir) as client:
            with local_test_infrastructure.user_token(scopes=['mpaf-read']) as user_token:
                rac = ResourceAPIClient(client, token=user_token['access_token'])

                (resp, resp_body) = rac.create(name='Unauthorised')
                assert resp.status_code == 401
                assert resp_body == {}

                (resp, resp_body) = rac.modify(1, name='Unauthorised')
                assert resp.status_code == 401

                (resp, resp_body) = rac.remove(1)
                assert resp.status_code == 401
                assert resp_body is None

    def test_duplicate_creation_fails(self, tmpdir, local_test_infrastructure):
        with local_test_infrastructure.app_client(tmpdir) as client:
            with local_test_infrastructure.user_token(scopes=['mpaf-read', 'mpaf-write']) as user_token:
                rac = ResourceAPIClient(client, token=user_token['access_token'])

                resource_name = f'Test Resource {datetime.utcnow()}'
                (resp, resp_body) = rac.create(name=resource_name)
                assert resp.status_code == 201
                assert resp_body['id'] is not None
                assert resp_body['name'] == resource_name

                (resp, resp_body) = rac.create(name=resource_name)
                assert resp.status_code == 409
                assert resp_body['code'] == 409
                assert resp_body['message'] == 'This resource already exists'

    def test_ownership_is_maintained(self, tmpdir, local_test_infrastructure):
        with local_test_infrastructure.app_client(tmpdir) as client, \
             local_test_infrastructure.user_token(user_id='test-user1', scopes=['mpaf-read', 'mpaf-write']) as token1, \
             local_test_infrastructure.user_token(user_id='test-user2', scopes=['mpaf-read', 'mpaf-write']) as token2:

            rac1 = ResourceAPIClient(client, token=token1['access_token'])
            rac2 = ResourceAPIClient(client, token=token2['access_token'])

            resource_name = f'Test Resource {datetime.utcnow()}'
            (resp, resp_body) = rac1.create(name=resource_name)
            assert resp.status_code == 201

            (resp, resp_body) = rac2.create(name=resource_name)
            assert resp.status_code == 201
            user2_resource = resp_body['id']

            (resp, resp_body) = rac1.modify(user2_resource, name='Test')
            assert resp.status_code == 401
            assert resp_body['code'] == 401
            assert resp_body['message'] == 'You are not authorised to modify this resource'

            (resp, resp_body) = rac1.remove(user2_resource)
            assert resp.status_code == 401
            assert resp_body['code'] == 401
            assert resp_body['message'] == 'You are not authorised to remove this resource'

