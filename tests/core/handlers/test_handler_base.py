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
import time
import clacks
import unittest
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class TestBaseHandler(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test__get_header_data(self):
        handler = clacks.BaseRequestHandler(clacks.SimplePackageMarshaller())

        try:
            # -- this should raise a NotImplementedError
            handler._get_header_data(
                transaction_id='',
                payload=clacks.package.Package(payload=dict()),
                header_data=dict()
            )
            self.fail()
        except NotImplementedError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_decode_question_header(self):
        handler = clacks.BaseRequestHandler(clacks.SimplePackageMarshaller())

        try:
            # -- this should raise a NotImplementedError
            handler.decode_question_header(
                transaction_id='',
                header=dict()
            )
            self.fail()
        except NotImplementedError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_question_header(self):
        handler = clacks.BaseRequestHandler(clacks.SimplePackageMarshaller())

        try:
            # -- this should raise a NotImplementedError
            handler.encode_question_header(transaction_id='', payload=None, expected_content_length=0)
            self.fail()
        except NotImplementedError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_decode_response_header(self):
        handler = clacks.BaseRequestHandler(clacks.SimplePackageMarshaller())

        try:
            # -- this should raise a NotImplementedError
            handler.decode_response_header(
                transaction_id='',
                header=dict()
            )
            self.fail()
        except NotImplementedError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_response_header(self):
        handler = clacks.BaseRequestHandler(clacks.SimplePackageMarshaller())

        try:
            # -- this should raise a NotImplementedError
            handler.encode_response_header(
                transaction_id='',
                payload=None,
                expected_content_length=0
            )
            self.fail()
        except NotImplementedError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_connection_keep_alive(self):
        # -- this transaction should ensure that the server handler manually keeps the connection alive, rather than
        # -- automatically doing so using the handler's built in recovery mechanisms.
        header_data, response = self.client.send(
            data=clacks.package.Question(header_data={'Connection': 'keep-alive'}, command='list_commands')
        )

        list(self.server.sockets.keys())[0].setblocking(False)
        list(self.server.sockets.keys())[0].settimeout(0.1)

        time.sleep(0.5)

        header_data, response = self.client.send(
            data=clacks.package.Question(header_data=dict(), command='list_commands')
        )
