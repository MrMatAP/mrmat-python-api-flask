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
Blueprint for the Greeting API in V1
"""

import logging

from flask_smorest import Blueprint
from mrmat_python_api_flask.apis.greeting.v1.model import greeting_v1_output, GreetingV1Output

bp = Blueprint('greeting_v1', __name__, description='Greeting V1 API')
log = logging.getLogger('api')


@bp.route('/', methods=['GET'])
@bp.response(200, GreetingV1Output)
@bp.doc(summary='Get an anonymous greeting',
        description='This version of the greeting API does not have a means to determine who you are')
def get_greeting():
    """
    Receive a Hello World message
    Returns:
        A plain-text hello world message
    """
    log.info('v1/helloworld')
    return greeting_v1_output.dump({'message': 'Hello World'}), 200
