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

"""Resource API SQLAlchemy model
"""

from sqlalchemy import ForeignKey, Column, Integer, String, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship

from mrmat_python_api_flask import db, ma


class Owner(db.Model):
    __tablename__ = 'owners'
    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True)
    client_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    resources = relationship('Resource', back_populates='owner')


class Resource(db.Model):
    __tablename__ = 'resources'
    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True)
    owner_id = Column(Integer, ForeignKey('owners.id'), nullable=False)
    name = Column(String(255), nullable=False)

    owner = relationship('Owner', back_populates='resources')
    UniqueConstraint('owner_id', 'name', name='no_duplicate_names_per_owner')


class OwnerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('id', 'client_id', 'name')


class ResourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('id', 'owner', 'name')


owner_schema = OwnerSchema()
owners_schema = OwnerSchema(many=True)
resource_schema = ResourceSchema()
resources_schema = ResourceSchema(many=True)
