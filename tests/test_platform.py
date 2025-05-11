#  MIT License
#
#  Copyright (c) 2021 Mathieu Imfeld
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

from mrmat_python_api_flask.apis.platform.v1 import (
    Owner,
    OwnerInput, owner_input_schema,
    owner_schema, owners_schema,
    Resource,
    ResourceInput, resource_input_schema,
    resource_schema, resources_schema
)

def test_platform_v1(client: flask.testing.Client):
    response = client.get('/api/platform/v1/owners')
    assert response.status_code == 200
    owners = owners_schema.load(response.json, many=True)
    assert isinstance(owners, list)
    assert len(owners) == 0

    owner = owner_input_schema.dump(OwnerInput(name='test-owner'))
    response = client.post('/api/platform/v1/owners', json=owner)
    assert response.status_code == 201
    owner_created = owner_schema.load(response.json)
    assert isinstance(owner_created, Owner)
    assert owner_created.uid is not None

    response = client.get(f'/api/platform/v1/owners/{owner_created.uid}')
    assert response.status_code == 200
    owner_retrieved = owner_schema.load(response.json)
    assert isinstance(owner_retrieved, Owner)
    assert owner_created.uid == owner_retrieved.uid
    assert owner_created.name == owner_retrieved.name

    response = client.get('/api/platform/v1/resources')
    assert response.status_code == 200
    resources = resources_schema.load(response.json)
    assert isinstance(resources, list)
    assert len(resources) == 0

    resource = resource_input_schema.dump(
        Resource(name='test-resource', owner_uid=owner_created.uid))
    response = client.post('/api/platform/v1/resources', json=resource)
    assert response.status_code == 201
    resource_created = resource_schema.load(response.json)
    assert isinstance(resource_created, Resource)
    assert resource_created.uid is not None
    assert resource_created.owner_uid == owner_created.uid

    response = client.get(f'/api/platform/v1/resources/{resource_created.uid}')
    assert response.status_code == 200
    resource_retrieved = resource_schema.load(response.json)
    assert isinstance(resource_retrieved, Resource)
    assert resource_created.uid == resource_retrieved.uid
    assert resource_created.name == resource_retrieved.name
    assert resource_created.owner_uid == resource_retrieved.owner_uid

    response = client.get('/api/platform/v1/owners')
    assert response.status_code == 200
    owners = owners_schema.load(response.json, many=True)
    assert isinstance(owners, list)
    assert len(owners) == 1

    response = client.get('/api/platform/v1/resources')
    assert response.status_code == 200
    resources = resources_schema.load(response.json)
    assert isinstance(resources, list)
    assert len(resources) == 1

    owner = owner_input_schema.dump(OwnerInput(name='modified-owner'))
    response = client.put(f'/api/platform/v1/owners/{owner_created.uid}', json=owner)
    assert response.status_code == 200
    owner_updated = owner_schema.load(response.json)
    assert isinstance(owner_updated, Owner)
    assert owner_updated.uid == owner_created.uid
    assert owner_updated.name == 'modified-owner'

    response = client.get(f'/api/platform/v1/resources/{resource_created.uid}')
    assert response.status_code == 200
    resource_retrieved = resource_schema.load(response.json)
    assert isinstance(resource_retrieved, Resource)
    assert resource_retrieved.owner_uid == owner_updated.uid

    resource = resource_input_schema.dump(
        ResourceInput(name='modified-resource', owner_uid=owner_updated.uid))
    response = client.put(f'/api/platform/v1/resources/{resource_created.uid}', json=resource)
    assert response.status_code == 200
    resource_updated = resource_schema.load(response.json)
    assert isinstance(resource_updated, Resource)
    assert resource_updated.uid == resource_created.uid
    assert resource_updated.owner_uid == owner_updated.uid

    response = client.delete(f'/api/platform/v1/resources/{resource_created.uid}')
    assert response.status_code == 204
    response = client.delete(f'/api/platform/v1/resources/{resource_created.uid}')
    assert response.status_code == 410

    response = client.delete(f'/api/platform/v1/owners/{owner_created.uid}')
    assert response.status_code == 204
    response = client.delete(f'/api/platform/v1/owners/{owner_created.uid}')
    assert response.status_code == 410
