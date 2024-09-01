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

"""Greeting API v1 Model"""

import dataclasses
from marshmallow import fields, post_load

from mrmat_python_api_flask import ma


@dataclasses.dataclass
class GreetingV1:
    """
    A dataclass containing the v1 greeting
    """
    message: str


class GreetingV1OutputSchema(ma.Schema):
    """
    The GreetingV1 Output Schema
    """
    class Meta:
        fields = ('message',)

    message = fields.Str(
        required=True,
        metadata={
            'description': 'A greeting message'
        }
    )

    @post_load
    def make_greeting_v1(self, data, **kwargs):
        return GreetingV1(**data)


greeting_v1_output_schema = GreetingV1OutputSchema()
