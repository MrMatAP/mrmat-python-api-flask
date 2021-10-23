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

"""Main entry point when executing this application from the CLI
"""

import sys
import argparse

from flask_migrate import upgrade

from mrmat_python_api_flask import __version__, create_app


def main() -> int:
    """
    Main entry point
    :return: Exit code
    """
    parser = argparse.ArgumentParser(description=f'mrmat-python-api-flask - {__version__}')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('--host',
                        dest='host',
                        required=False,
                        default='localhost',
                        help='Host interface to bind to')
    parser.add_argument('--port',
                        dest='port',
                        required=False,
                        default=8080,
                        help='Port to bind to')
    parser.add_argument('--instance-path',
                        dest='instance_path',
                        required=False,
                        default=None,
                        help='Fully qualified path to instance directory')
    parser.add_argument('--db',
                        dest='db',
                        required=False,
                        default=None,
                        help='Database URI')
    parser.add_argument('--oidc-secrets',
                        dest='oidc_secrets',
                        required=False,
                        help='Path to file containing OIDC registration')

    args = parser.parse_args()

    overrides = {'DEBUG': args.debug}
    if args.oidc_secrets is not None:
        overrides['OIDC_CLIENT_SECRETS'] = args.oidc_secrets
    if args.db is not None:
        overrides['SQLALCHEMY_DATABASE_URI'] = args.db

    app = create_app(config_override=overrides, instance_path=args.instance_path)
    with app.app_context():
        upgrade()
    app.run(host=args.host, port=args.port, debug=args.debug)

    return 0


if __name__ == '__main__':
    sys.exit(main())
