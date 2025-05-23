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

"""Greeting API v2 Model"""

import dataclasses
from marshmallow import fields, post_load

from mrmat_python_api_flask import ma

@dataclasses.dataclass
class GreetingV2Input:
    name: str = dataclasses.field(default='Stranger')

class GreetingV2InputSchema(ma.Schema):
    """
    The GreetingV2 Input Schema
    """
    class Meta:
        fields: ('name',)

    name = fields.Str(
        required=False,
        load_only=True,
        load_default='Stranger',
        metadata={
            'description': 'The optional name to greet'
        }
    )

    @post_load
    def as_object(self, data, **kwargs) -> GreetingV2Input:
        return GreetingV2Input(**data)

@dataclasses.dataclass
class GreetingV2:
    message: str = dataclasses.field(default='Hello Stranger')

class GreetingV2Schema(ma.Schema):
    """
    The GreetingV2 Output Schema
    """
    class Meta:
        fields = ('message',)

    message = fields.Str(
        required=True,
        metadata={
            'description': 'A customizable greeting message'
        }
    )

    @post_load
    def as_object(self, data, **kwargs) -> GreetingV2:
        return GreetingV2(**data)


greeting_v2_input_schema = GreetingV2InputSchema()
greeting_v2_schema = GreetingV2Schema()
