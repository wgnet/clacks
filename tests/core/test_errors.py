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


# ----------------------------------------------------------------------------------------------------------------------
class TestClacksErrors(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_error_type(self):
        class NewErrorType(Exception):
            pass

        clacks.register_error_type('new', NewErrorType)

        assert clacks.error_from_key('new') is NewErrorType
        assert clacks.key_from_error_type(NewErrorType) == 'new'

    # ------------------------------------------------------------------------------------------------------------------
    def test_request_invalid_error_type(self):
        try:
            clacks.key_from_error_type(None)
            self.fail()
        except KeyError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_invalid_error_type(self):
        class InvalidErrorType(object):
            pass

        try:
            clacks.register_error_type('invalid', InvalidErrorType)
            self.fail()
        except TypeError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_invalid_key(self):
        class ValidErrorType(Exception):
            pass

        try:
            clacks.register_error_type('__invalid/key--', ValidErrorType)
            self.fail()
        except KeyError:
            pass
