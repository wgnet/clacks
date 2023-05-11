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
class TestSimpleRequestHandler(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def question(cls):
        return clacks.package.Question(
            header_data=dict(),
            command='foo',
            **{'test': 'value', 'integer': 0, 'float': 0.2}
        )

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_question_header(self):
        handler = clacks.handler.SimpleRequestHandler(clacks.SimplePackageMarshaller())
        handler._initialize(self)
        length = handler.get_content_length('', self.question())
        response = handler.encode_question_header('UNITTEST', self.question(), length)
        assert isinstance(response, bytes)

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_response_header(self):
        handler = clacks.handler.SimpleRequestHandler(clacks.SimplePackageMarshaller())
        handler._initialize(self)
        length = handler.get_content_length('', self.question())
        response = handler.encode_question_header('UNITTEST', self.question(), length)
        assert isinstance(response, bytes)
