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
Blueprint for the Healthz API
"""

from flask_smorest import Blueprint

from .model import (
    Healthz, HealthzSchema, healthz_schema,
    Liveness, LivenessSchema, liveness_schema,
    Readiness, ReadinessSchema, readiness_schema
)

bp = Blueprint('healthz', __name__, description='Health API')


@bp.route('/', methods=['GET'])
@bp.response(200, HealthzSchema)
@bp.doc(summary='Get an indication of overall application health',
        description='Assess application health')
def healthz() -> HealthzSchema:
    """
    Respond with the app health status
    Returns:
        A status response
    """
    return healthz_schema.dump(Healthz(status='OK'))


@bp.route('/liveness', methods=['GET'])
@bp.response(200, LivenessSchema)
@bp.doc(summary='Get an indication of application liveness',
        description='Assess application liveness')
def liveness() -> LivenessSchema:
    """
    Respond with the app health status
    Returns:
        A status response
    """
    return liveness_schema.dump(Liveness(status='OK'))

@bp.route('/readiness', methods=['GET'])
@bp.response(200, ReadinessSchema)
@bp.doc(summary='Get an indication of application readiness',
        description='Assess application liveness')
def readiness() -> ReadinessSchema:
    """
    Respond with the app health status
    Returns:
        A status response
    """
    return readiness_schema.dump(Readiness(status='OK'))
