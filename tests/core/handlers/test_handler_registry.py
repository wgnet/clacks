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
import clacks
import unittest
from clacks.core.handler import register_handler_type, handler_from_key


class TestHandler(clacks.BaseRequestHandler):

    def _get_header_data(self, transaction_id, payload, header_data):
        pass

    def decode_question_header(self, transaction_id, header):
        pass

    def encode_question_header(self, transaction_id, payload, expected_content_length):
        pass

    def decode_response_header(self, transaction_id, header):
        pass

    def encode_response_header(self, transaction_id, payload, expected_content_length):
        pass


class TestHandlerRegistry(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_handler_type(self):
        # -- we do not allow illegal keys (this one contains a number)
        try:
            register_handler_type('illegal_1', None)
            self.fail()
        except KeyError:
            pass

        # -- we do not allow registering the base class as a valid handler type
        try:
            register_handler_type('good_key', clacks.BaseRequestHandler)
            self.fail()
        except ValueError:
            pass

        # -- this should succeed
        register_handler_type('unittest', TestHandler)

    # ------------------------------------------------------------------------------------------------------------------
    def test_handler_from_type(self):
        try:
            handler = handler_from_key('foobar')
            self.fail()
        except KeyError:
            pass

        # -- the simple handler is always registered.
        handler = handler_from_key('simple')
