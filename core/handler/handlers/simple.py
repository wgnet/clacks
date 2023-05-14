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

from ...handler.base import BaseRequestHandler
from ...handler.constants import register_handler_type
from ...marshaller.marshallers.simple import decode_package, encode_package
from ...package import Package, Question, Response


# ----------------------------------------------------------------------------------------------------------------------
class SimpleRequestHandler(BaseRequestHandler):

    # ------------------------------------------------------------------------------------------------------------------
    def _get_header_data(self, transaction_id, payload, header_data):
        # type: (str, Package, collections.OrderedDict) -> collections.OrderedDict
        return collections.OrderedDict()

    # ------------------------------------------------------------------------------------------------------------------
    def decode_question_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        return decode_package(header, self.FORMAT)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_question_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> bytes
        if not isinstance(payload, Question):
            raise ValueError(f'Expected Question, got {payload}')

        if not payload.is_valid:
            raise ValueError(f'Invalid Package instance provided: {payload}!')

        content_length = self.get_content_length(transaction_id, payload)

        if content_length != expected_content_length:
            raise ValueError(
                'expected: {expected} / got: {got} ; '
                'Encoded content length and expected content length are not matching!'.format(
                    expected=expected_content_length,
                    got=content_length
                )
            )

        data = dict()
        data['Content-Length'] = content_length
        data.update(Connection=payload.payload.get('header_data', dict()).get('Connection'))
        buffer = encode_package(data, self.FORMAT)

        return buffer

    # ------------------------------------------------------------------------------------------------------------------
    def decode_response_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        return decode_package(header, self.FORMAT)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_response_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Response, int) -> bytes
        if not isinstance(payload, Response):
            raise ValueError(f'Expected Response, got {payload}')

        if not payload.is_valid:
            raise ValueError(f'Invalid Package instance provided: {payload}!')

        content_length = self.get_content_length(transaction_id, payload)
        if content_length != expected_content_length:
            raise ValueError('Encoded content length and expected content length are not matching!')

        data = dict()
        data['Content-Length'] = content_length
        data.update(Connection=payload.payload.get('header_data', dict()).get('Connection'))
        buffer = encode_package(data, self.FORMAT)

        return buffer


register_handler_type('simple', SimpleRequestHandler)
