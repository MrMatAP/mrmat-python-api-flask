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

from typing import Tuple

from werkzeug.local import LocalProxy
from flask import request, g, current_app
from flask_smorest import Blueprint
from marshmallow import ValidationError

from mrmat_python_api_flask import db, oidc
from mrmat_python_api_flask.apis import status_output
from .model import Owner, Resource, ResourceSchema, OwnerSchema, resource_schema, resources_schema

bp = Blueprint('resource_v1', __name__, description='Resource V1 API')
logger = LocalProxy(lambda: current_app.logger)


def _extract_identity() -> Tuple:
    return g.oidc_token_info['client_id'], \
           g.oidc_token_info['username']


@bp.route('/', methods=['GET'])
@bp.doc(summary='Get all known resources',
        description='Returns all currently known resources and their metadata',
        security=[{'openId': ['mpaf-read']}])
@bp.response(200, schema=ResourceSchema(many=True))
@oidc.accept_token(require_token=True, scopes_required=['mpaf-read'])
def get_all():
    (client_id, name) = _extract_identity()
    logger.info(f'Called by {client_id} for {name}')
    a = Resource.query.all()
    return {'resources': resources_schema.dump(a)}, 200


@bp.route('/<i>', methods=['GET'])
@bp.doc(summary='Get a single resource',
        description='Return a single resource identified by its resource id.',
        security=[{'openId': ['mpaf-read']}])
@bp.response(200, schema=ResourceSchema)
@oidc.accept_token(require_token=True, scopes_required=['mpaf-read'])
def get_one(i: int):
    (client_id, name) = _extract_identity()
    logger.info(f'Called by {client_id} for {name}')
    resource = Resource.query.filter(Resource.id == i).one_or_none()
    if resource is None:
        return status_output.dump(code=404, message='Unable to find a resource with this id'), 404
    return resource_schema.dump(resource), 200


@bp.route('/', methods=['POST'])
@bp.doc(summary='Create a resource',
        description='Create a resource owned by the authenticated user',
        security=[{'openId':['mpaf-write']}])
@bp.arguments(ResourceSchema,
              location='json',
              required=True,
              description='The resource to create')
@bp.response(200, schema=ResourceSchema)
@oidc.accept_token(require_token=True, scopes_required=['mpaf-write'])
def create():
    (client_id, name) = _extract_identity()
    logger.info(f'Called by {client_id} for {name}')
    try:
        json_body = request.get_json()
        if not json_body:
            return status_output.dump(code=400, message='Missing input data'), 400
        body = resource_schema.load(request.get_json())
    except ValidationError as ve:
        return ve.messages, 422

    #
    # Check if we have a resource with the same name and owner already

    resource = Resource.query\
        .filter(Resource.name == body['name'] and Resource.owner.client_id == client_id)\
        .one_or_none()
    if resource is not None:
        # TODO: Allow turning this off because it can be used as an enumeration attack
        return status_output.dump(code=409, message='This resource already exists'), 409

    #
    # Look up the owner and create one if necessary

    owner = Owner.query.filter(Owner.client_id == client_id).one_or_none()
    if owner is None:
        owner = Owner(client_id=client_id, name=name)
        db.session.add(owner)

    resource = Resource(owner=owner, name=body['name'])
    db.session.add(resource)
    db.session.commit()
    return resource_schema.dump(resource), 201


@bp.route('/<i>', methods=['PUT'])
@oidc.accept_token(require_token=True, scopes_required=['mpaf-write'])
def modify(i: int):
    (client_id, name) = _extract_identity()
    logger.info(f'Called by {client_id} for {name}')
    body = resource_schema.load(request.get_json())

    resource = Resource.query.filter(Resource.id == i).one_or_none()
    if resource is None:
        return status_output.dump(code=404, message='Unable to find a resource with this id'), 404
    if resource.owner.client_id != client_id:
        return status_output.dump(code=401, message='You are not authorised to modify this resource'), 401
    resource.name = body['name']

    db.session.add(resource)
    db.session.commit()
    return resource_schema.dump(resource), 200


@bp.route('/<i>', methods=['DELETE'])
@oidc.accept_token(require_token=True, scopes_required=['mpaf-write'])
def remove(i: int):
    (client_id, name) = _extract_identity()
    logger.info(f'Called by {client_id} for {name}')

    resource = Resource.query.filter(Resource.id == i).one_or_none()
    if resource is None:
        # TODO: Allow turning this off because it can be used as an enumeration attack
        return status_output.dump(code=410, message='The resource is gone'), 410
    if resource.owner.client_id != client_id:
        return status_output.dump(code=401, message='You are not authorised to remove this resource'), 401

    db.session.delete(resource)
    db.session.commit()
    return {}, 204
