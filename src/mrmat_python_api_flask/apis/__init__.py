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
Code that can be re-used by all APIs
"""

import dataclasses
from marshmallow import fields, post_load

from mrmat_python_api_flask import ma

@dataclasses.dataclass
class Status:
    code: int = dataclasses.field(default=500)
    msg: str = dataclasses.field(default='An unknown error occurred')

class StatusSchema(ma.Schema):
    """
    A generic message class
    """
    code = fields.Int(
        required=True,
        metadata={
            'description': 'An integer status code which will typically match the HTTP status code'
        })

    msg = fields.Str(
        required=True,
        metadata={
            'description': 'A human-readable message'
        }
    )

    @post_load
    def as_object(self, data, **kwargs) -> Status:
        return Status(**data)

status_schema = StatusSchema()
