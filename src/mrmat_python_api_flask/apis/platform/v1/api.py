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

"""Blueprint for the Resource API in V1
"""
import uuid
from typing import Tuple

from flask import g, jsonify
from flask_smorest import Blueprint
from sqlalchemy.exc import SQLAlchemyError

from mrmat_python_api_flask import db
from mrmat_python_api_flask.apis import Status, status_schema
from .model import (
    Owner, Resource,
    OwnerInput, OwnerInputSchema,
    OwnerSchema, owner_schema, owners_schema,
    ResourceInput, ResourceInputSchema,
    ResourceSchema, resource_schema, resources_schema
)

bp = Blueprint('platform_v1', __name__, description='Platform V1 API')

@bp.errorhandler(SQLAlchemyError)
def db_error(e):
    return jsonify(error=str(e)), 500


def _extract_identity() -> Tuple:
    return g.oidc_token_info['client_id'], g.oidc_token_info['username']


@bp.route('/resources', methods=['GET'])
@bp.doc(summary='Get all known resources',
        description='Returns all currently known resources and their metadata',
        security=[{'openId': ['mpaflask-read']}])
@bp.response(200, schema=ResourceSchema(many=True))
def get_resources():
    #(client_id, name) = _extract_identity()
    resources = db.session.query(Resource).all()
    return resources_schema.dump(
        [Resource(uid=r.uid, name=r.name, owner_uid=r.owner_uid) for r in resources]
    ), 200


@bp.route('/resources/<string:uid>', methods=['GET'])
@bp.doc(summary='Get a single resource',
        description='Return a single resource identified by its resource id',
        security=[{'openId': ['mpaflask-read']}])
@bp.response(200, schema=ResourceSchema)
def get_resource(uid: str):
    #(client_id, name) = _extract_identity()
    resource = db.session.get(Resource, uid)
    if not resource:
        return status_schema.dump(Status(code=404, msg='No such resource')), 404
    return resource_schema.dump(resource), 200


@bp.route('/resources', methods=['POST'])
@bp.doc(summary='Create a resource',
        description='Create a resource owned by the authenticated user',
        security=[{'openId': ['mpaflask-write']}])
@bp.arguments(ResourceInputSchema,
              location='json',
              required=True,
              description='The resource to create')
@bp.response(201, schema=ResourceSchema)
def create_resource(data: ResourceInput):
    #(client_id, name) = _extract_identity()
    resource = Resource(uid=str(uuid.uuid4()), name=data.name, owner_uid=str(data.owner_uid))
    db.session.add(resource)
    db.session.commit()
    return resource_schema.dump(resource), 201

@bp.route('/resources/<string:uid>', methods=['PUT'])
@bp.doc(summary='Modify a resource',
        description='Modify a resource owned by the authenticated user',
        security=[{'openId': ['mpaflask-write']}])
@bp.arguments(ResourceInputSchema,
              location='json',
              required=True,
              description='The resource with updated contents')
@bp.response(200, schema=ResourceSchema)
def modify_resource(data: ResourceInput, uid: str):
    #(client_id, name) = _extract_identity()
    resource = db.session.get(Resource, uid)
    if not resource:
        return status_schema.dump(Status(code=404, msg='No such resource')), 404
    resource.name = data.name
    db.session.add(resource)
    db.session.commit()
    return resource_schema.dump(resource), 200

@bp.route('/resources/<string:uid>', methods=['DELETE'])
@bp.doc(summary='Remove a resource',
        description='Remove a resource owned by the authenticated user',
        security=[{'openId': ['mpaflask-write']}])
def remove_resource(uid: str):
    #(client_id, name) = _extract_identity()
    resource = db.session.get(Resource, uid)
    if not resource:
        return status_schema.dump(Status(code=410, msg='The resource was already gone')), 410
    db.session.delete(resource)
    db.session.commit()
    return {}, 204

@bp.route('/owners', methods=['GET'])
@bp.doc(summary='Get all owners',
        description='Get all currently known owners',
        security=[{'openId': ['mpaflask-read']}])
@bp.response(200, schema=OwnerSchema(many=True))
def get_owners():
    #(client_id, name) = _extract_identity()
    owners = db.session.query(Owner).all()
    return owners_schema.dump([Owner(uid=r.uid, name=r.name) for r in owners]), 200

@bp.route('/owners/<string:uid>', methods=['GET'])
@bp.doc(summary='Get a single owner',
        description='Return a single owner identified by its owner id',
        security=[{'openId': ['mpaflask-read']}])
@bp.response(200, schema=OwnerSchema)
def get_owner(uid: str):
    #(client_id, name) = _extract_identity()
    owner = db.session.get(Owner, uid)
    if not owner:
        return status_schema.dump(Status(code=404, msg='No such owner')), 404
    return owner_schema.dump(owner), 200

@bp.route('/owners', methods=['POST'])
@bp.doc(summary='Create an owner',
        description='Create an owner',
        security=[{'openId': ['mpaflask-write']}])
@bp.arguments(OwnerInputSchema,
              location='json',
              required=True,
              description='The owner to create')
@bp.response(201, schema=OwnerSchema)
def create_owner(data: OwnerInput):
    #(client_id, name) = _extract_identity()
    owner = Owner(uid=str(uuid.uuid4()), name=data.name)
    db.session.add(owner)
    db.session.commit()
    return owner_schema.dump(owner), 201

@bp.route('/owners/<string:uid>', methods=['PUT'])
@bp.doc(summary='Modify an owner',
        description='Modify an owner',
        security=[{'openId': ['mpaflask-write']}])
@bp.arguments(OwnerInputSchema,
              location='json',
              required=True,
              description='The owner with updated contents')
@bp.response(200, schema=OwnerSchema)
def modify_owner(data: OwnerInput, uid: str):
    #(client_id, name) = _extract_identity()
    owner = db.session.get(Owner, uid)
    if not owner:
        return status_schema.dump(Status(code=404, msg='No such owner')), 404
    owner.name = data.name
    db.session.add(owner)
    db.session.commit()
    return owner_schema.dump(owner), 200

@bp.route('/owners/<string:uid>', methods=['DELETE'])
@bp.doc(summary='Remove an owner',
        description='Remove an owner',
        security=[{'openId': ['mpaflask-write']}])
def remove_owner(uid: str):
    #(client_id, name) = _extract_identity()
    owner = db.session.get(Owner, uid)
    if not owner:
        return status_schema.dump(Status(code=410, msg='The owner was already gone')), 410
    db.session.delete(owner)
    db.session.commit()
    return {}, 204
