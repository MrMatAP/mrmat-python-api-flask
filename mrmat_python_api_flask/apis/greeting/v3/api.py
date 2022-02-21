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
Blueprint for the Greeting API in V3
"""

from flask import g
from flask_smorest import Blueprint

from mrmat_python_api_flask import oidc
from .model import greeting_v3_output, GreetingV3Output

bp = Blueprint('greeting_v3', __name__, description='Greeting V3 API')


@bp.route('/', methods=['GET'])
@bp.response(200, schema=GreetingV3Output)
@bp.doc(summary='Get a greeting for the authenticated name',
        description='This version of the greeting API knows who you are',
        security=[{'openId': ['profile']}])
@oidc.accept_token(require_token=True)
def get():
    """
    Get a named greeting for the authenticated user
    Returns:
        A named greeting in JSON
    """
    return greeting_v3_output.dump(dict(message=f'Hello {g.oidc_token_info["username"]}')), 200
