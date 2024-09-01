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

from typing import Optional
from marshmallow import fields

from mrmat_python_api_flask import ma


class StatusOutputSchema(ma.Schema):
    """
    A schema for a generic status message returned via HTTP
    """
    class Meta:
        fields = ('code', 'message')

    code = fields.Int(
        default=200,
        metadata={
            'description': 'An integer status code which will typically match the HTTP status code'
        }
    )
    message = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            'description': 'A human-readable message'
        }
    )

    def __init__(self, code: Optional[int] = 200, message: Optional[str] = 'OK'):
        super().__init__()
        self.code = code
        self.message = message


status_output = StatusOutputSchema()


def status(code: Optional[int] = 200, message: Optional[str] = 'OK') -> dict:
    """
    A utility to return a standardised HTTP status message
    Args:
        code: Status code, typically matches the HTTP status code
        message: Human-readable message

    Returns:
        A dict to be rendered into JSON
    """
    status_message = StatusOutputSchema(code=code, message=message)
    return status_output.dump(status_message)
