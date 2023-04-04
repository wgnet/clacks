"""
Copyright 2022-2023 Wargaming.net

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import collections
import json

from ...handler import BaseRequestHandler
from ...handler import register_handler_type
from ....core.package import Package, Question, Response


# ----------------------------------------------------------------------------------------------------------------------
class JSONHandler(BaseRequestHandler):

    # ------------------------------------------------------------------------------------------------------------------
    def _get_header_data(self, transaction_id, payload, header_data):
        # type: (str, Package, collections.OrderedDict) -> collections.OrderedDict
        if not isinstance(payload, Package):
            raise ValueError('Expected Package instance, got %s!' % payload)

        result = collections.OrderedDict()

        result['Content-Length'] = self.get_content_length(transaction_id, payload)
        result['Accept-Encoding'] = payload.accept_encoding

        if payload.keep_alive:
            result['Connection'] = 'keep-alive'

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def decode_question_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        if not isinstance(header, str):
            data = str(header, self.FORMAT)
        else:
            data = str(header)
        return json.loads(data)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_question_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> bytes
        if not isinstance(payload, Question):
            raise ValueError('Expected Question, got %s' % payload)

        result = json.dumps(
            self.get_outgoing_header_data(transaction_id, payload, expected_content_length),
            sort_keys=True
        )

        return result.encode('utf-8')

    # ------------------------------------------------------------------------------------------------------------------
    def decode_response_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        if not isinstance(header, str):
            data = str(header, self.FORMAT)
        else:
            data = str(header)
        return json.loads(data)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_response_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Response, int) -> bytes
        if not isinstance(payload, Response):
            raise ValueError('Expected Response, got %s' % payload)

        response = json.dumps(
            self.get_outgoing_header_data(transaction_id, payload, expected_content_length), sort_keys=True
        )

        return response.encode('utf-8')


register_handler_type('json', JSONHandler)
