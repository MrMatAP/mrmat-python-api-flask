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
Blueprint for the Greeting API in V2
"""

from flask_smorest import Blueprint
from .model import (
    GreetingV2Input, GreetingV2InputSchema, greeting_v2_input_schema,
    GreetingV2, GreetingV2Schema, greeting_v2_schema
)

bp = Blueprint('greeting_v2', __name__, description='Greeting V2 API')


@bp.route('/', methods=['GET'])
@bp.arguments(GreetingV2InputSchema,
              description='The name to greet',
              location='query',
              required=False)
@bp.response(200, GreetingV2Schema)
@bp.doc(summary='Get a greeting for a given name',
        description='This version of the greeting API allows you to specify who to greet')
def get(greeting_input: GreetingV2Input) -> GreetingV2Schema:
    """
    Get a named greeting
    Returns:
        A named greeting in JSON
    """
    safe_name: str = greeting_input.name or 'Stranger'
    return greeting_v2_schema.dump(obj=GreetingV2(message=f'Hello {safe_name}'))
