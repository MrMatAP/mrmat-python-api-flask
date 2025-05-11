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
import dataclasses

from marshmallow import fields, post_load
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mrmat_python_api_flask import ma, ORMBase


class Owner(ORMBase):
    __tablename__ = 'owners'
    __schema__ = 'mrmat-python-api-flask'
    uid: Mapped[str] = mapped_column(String, primary_key=True)

    client_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resources: Mapped[list["Resource"]] = relationship('Resource', back_populates='owner')

class Resource(ORMBase):
    __tablename__ = 'resources'
    __schema__ = 'mrmat-python-api-flask'
    uid: Mapped[str] = mapped_column(String, primary_key=True)
    owner_uid: Mapped[str] = mapped_column(String, ForeignKey('owners.uid'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    owner: Mapped["Owner"] = relationship('Owner', back_populates='resources')
    __table_args__ = (UniqueConstraint('owner_uid', 'name', name='no_duplicate_names_per_owner'),)


class OwnerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Owner

    uid = ma.auto_field()
    client_id = ma.auto_field()
    name = ma.auto_field()

    @post_load
    def as_object(self, data, **kwargs):
        return Owner(**data)

@dataclasses.dataclass
class OwnerInput:
    name: str

class OwnerInputSchema(ma.Schema):
    name = fields.Str(
        required=True,
        metadata={
            'description': 'The owner\'s name'
        })

    @post_load
    def as_object(self, data, **kwargs):
        return OwnerInput(**data)

class ResourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Resource
        include_fk = True
    uid = ma.auto_field()
    owner_uid = ma.auto_field()
    name = ma.auto_field()

    @post_load
    def as_object(self, data, **kwargs):
        return Resource(**data)

@dataclasses.dataclass
class ResourceInput:
    name: str
    owner_uid: str

class ResourceInputSchema(ma.Schema):
    name = fields.String(
        required=True,
        metadata={
            'description': 'The resource name'
        })
    owner_uid = fields.Str(
        required=True,
        metadata={
            'description': 'The owner UID'
        })

    @post_load
    def as_object(self, data, **kwargs):
        return ResourceInput(**data)
owner_schema = OwnerSchema()
owners_schema = OwnerSchema(many=True)
owner_input_schema = OwnerInputSchema()
resource_schema = ResourceSchema()
resources_schema = ResourceSchema(many=True)
resource_input_schema = ResourceInputSchema()
