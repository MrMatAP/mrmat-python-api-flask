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

"""Main entry point of the interactive client application
"""

import os.path
import sys
import json
from time import sleep
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict
import requests

from mrmat_python_api_flask import __version__, log


class ClientException(Exception):
    """A simple exception subclass

    Just so we can distinguish ourselves from whatever else may be thrown and capture an ultimate exit code and
    error message
    """
    exit_code: int
    msg: str

    def __init__(self, exit_code: int = 1, msg: str = 'Unknown Exception'):
        Exception.__init__()
        self.exit_code = exit_code
        self.msg = msg


def oidc_discovery(config: Dict) -> Dict:
    resp = requests.get(config['discovery_url'], timeout=60)
    if resp.status_code != 200:
        raise ClientException(exit_code=1, msg=f'Unexpected response {resp.status_code} from discovery endpoint')
    try:
        data = resp.json()
    except ValueError as ve:
        raise ClientException(exit_code=1, msg='Unable to parse response from discovery endpoint into JSON') from ve
    return data


def oidc_device_auth(config: Dict, discovery: Dict) -> Dict:
    resp = requests.post(url=discovery['device_authorization_endpoint'],
                         data={'client_id': config['client_id'],
                               'client_secret': config['client_secret'],
                               'scope': ['openid', 'profile']},
                         timeout=60)
    if resp.status_code != 200:
        raise ClientException(exit_code=1, msg=f'Unexpected response {resp.status_code} from device endpoint')
    try:
        data = resp.json()
    except ValueError as ve:
        raise ClientException(exit_code=1, msg='Unable to parse response from device endpoint into JSON') from ve
    return data


def oidc_check_auth(config: Dict, discovery: Dict, device_auth: Dict):
    wait = 5
    stop = False
    while not stop:
        resp = requests.post(url=discovery['token_endpoint'],
                             data={'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                   'device_code': device_auth['device_code'],
                                   'client_id': config['client_id'],
                                   'client_secret': config['client_secret']},
                             timeout=60)  # client_secret only for keycloak
        if resp.status_code == 400:
            body = resp.json()
            if body['error'] == 'authorization_pending':
                continue
            elif body['error'] == 'slow_down':
                wait += 5
                continue
            elif body['error'] == 'access_denied':
                raise ClientException(msg='Access denied')
            elif body['error'] == 'expired_token':
                raise ClientException(msg='Token expired')
            else:
                raise ClientException(msg=body['error_description'])
        elif resp.status_code == 200:
            return resp.json()
        log.info('Waiting for %s seconds', wait)
        sleep(wait)


def parse_args(argv: List[str]) -> Optional[Namespace]:
    """A dedicated function to parse the command line arguments.

    Makes it a lot easier to test CLI parameters.

    Args:
        argv: The command line arguments, minus the name of the script

    Returns:
        The Namespace object as defined by the argparse module built-in to Python
    """
    parser = ArgumentParser(description=f'mrmat-python-api-flask-client - {__version__}')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', help='Silent Operation')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')

    parser.add_argument('--host',
                        dest='host',
                        required=False,
                        default='localhost',
                        help='Host interface to connect to')
    parser.add_argument('--port',
                        dest='port',
                        required=False,
                        default=8080,
                        help='Port to connect to')

    config_group_file = parser.add_argument_group(title='File Configuration',
                                                  description='Configure the client via a config file')
    config_group_file.add_argument('--config', '-c',
                                   dest='config',
                                   required=False,
                                   default=os.path.expanduser(os.path.join('~',
                                                                           'etc',
                                                                           'mrmat-python-api-flask-client.json')),
                                   help='Path to the configuration file for the flask client')

    config_group_manual = parser.add_argument_group(title='Manual Configuration',
                                                    description='Configure the client manually')
    config_group_manual.add_argument('--client-id',
                                     dest='client_id',
                                     required=False,
                                     help='The client_id of this CLI itself (not yours!)')
    config_group_manual.add_argument('--client-secret',
                                     dest='client_secret',
                                     required=False,
                                     help='The client_secret of the CLI itself. Not required for AAD, required for '
                                          'Keycloak')
    config_group_manual.add_argument('--discovery-url',
                                     dest='discovery_url',
                                     required=False,
                                     help='Discovery of endpoints in the authentication platform')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Main entry point for the CLI

    Args:
        argv: The command line arguments. These default to None and if so, the function will fall back to use the
              command line arguments without the application name used to invoke (i.e. sys.argv[1:])

    Returns:
        Exit code 0 for success. Any other integer is a failure.
    """
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args is None:
        return 0

    #
    # Read from the config file by default, but allow overrides via the CLI

    config = {}
    if os.path.exists(os.path.expanduser(args.config)):
        with open(os.path.expanduser(args.config), encoding='UTF-8') as c:
            config = json.load(c)
    config_override = vars(args)
    for key in config_override.keys() & config_override.keys():
        if config_override[key] is not None:
            config[key] = config_override[key]

    try:
        discovery = oidc_discovery(config)
        if 'device_authorization_endpoint' not in discovery:
            raise ClientException(msg='No device_authorization_endpoint in discovery')
        if 'token_endpoint' not in discovery:
            raise ClientException(msg='No token_endpoint in discovery')

        device_auth = oidc_device_auth(config, discovery)
        if 'device_code' not in device_auth:
            raise ClientException(msg='No device_code in device auth')
        if 'user_code' not in device_auth:
            raise ClientException(msg='No user_code in device auth')
        if 'verification_uri' not in device_auth:
            raise ClientException(msg='No verification_uri in device_auth')
        if 'expires_in' not in device_auth:
            raise ClientException(msg='No expires_in in device_auth')

        # Adding the user code to the URL is convenient, but not as secure as it could be
        log.info('Please visit %s within %s seconds and enter code %s. Or just visit %s',
                 device_auth['verification_uri'],
                 device_auth['expires_in'],
                 device_auth['user_code'],
                 device_auth['verification_uri_complete'])

        auth = oidc_check_auth(config, discovery, device_auth)
        log.info('Authenticated')

        #
        # We're using requests directly here because requests_oauthlib doesn't support device code flow directly

        resp = requests.get(f'http://{args.host}:{args.port}/api/greeting/v3/',
                            headers={'Authorization': f'Bearer {auth["id_token"]}'},
                            timeout=60)
        log.info('Status Code: %s', resp.status_code)
        log.info(resp.content)

        return 0
    except ClientException as ce:
        log.error(ce.msg)
        return ce.exit_code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
