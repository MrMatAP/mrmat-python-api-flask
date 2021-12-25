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

from flask import Response
from flask.testing import FlaskClient
from typing import Tuple, Dict, Optional


class ResourceAPIClient:
    client: FlaskClient
    token: Dict

    _headers: Dict = {}

    def __init__(self, client: FlaskClient, token: Optional[Dict]):
        self.client = client
        self.token = token
        if token is not None:
            self._headers = {'Authorization': f'Bearer {token["access_token"]}'}

    def get_all(self) -> Tuple:
        resp: Response = self.client.get('/api/resource/v1/', headers=self._headers)
        resp_body = self._parse_body(resp)
        return resp, resp_body

    def get_one(self, i: Optional[int]) -> Tuple:
        resp: Response = self.client.get(f'/api/resource/v1/{i}', headers=self._headers)
        resp_body = self._parse_body(resp)
        return resp, resp_body

    def create(self, name: str) -> Tuple:
        req_body = {'name': name}
        resp: Response = self.client.post('/api/resource/v1/', json=req_body, headers=self._headers)
        resp_body = self._parse_body(resp)
        return resp, resp_body

    def modify(self, i: Optional[int], name: str) -> Tuple:
        req_body = {'name': name}
        resp: Response = self.client.put(f'/api/resource/v1/{i}', json=req_body, headers=self._headers)
        resp_body = self._parse_body(resp)
        return resp, resp_body

    def remove(self, i: Optional[int]) -> Tuple:
        resp: Response = self.client.delete(f'/api/resource/v1/{i}', headers=self._headers)
        resp_body = self._parse_body(resp)
        return resp, resp_body

    @staticmethod
    def _parse_body(resp: Optional[Response]) -> Dict:
        # TODO: silent will return None if parsing fails. We may wish to know if the JSON is invalid vs no body/mime
        body = resp.get_json(silent=True)
        return body
