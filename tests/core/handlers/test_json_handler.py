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
import json
import clacks
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class TestJSONHandler(ClacksTestCase):

    handler_type = clacks.JSONHandler
    marshaller_type = clacks.JSONMarshaller

    # ------------------------------------------------------------------------------------------------------------------
    def test_decode_question_header(self):
        # -- the header should properly encode and decode the test data atomically
        data = self.create_handler().decode_question_header('UNITTEST', json.dumps(self.example_header_data()))
        assert data == self.example_header_data()

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_question_header(self):
        handler = self.create_handler()

        question = clacks.package.Question(
            header_data=self.example_header_data(),
            command='FOO'
        )

        length = handler.get_content_length('', question)
        data = handler.encode_question_header('UNITTEST', question, length)

        header_data = json.loads(data)

        assert header_data['Content-Length'] is len(json.dumps(question.payload))
        assert header_data['Connection'] == 'keep-alive'
        assert header_data['Accept-Encoding'] == 'text/json'

        new_question = clacks.package.Question(
            header_data=self.example_header_data(keep_alive=False),
            command='FOO'
        )

        length = handler.get_content_length('', new_question)
        new_data = handler.encode_question_header('UNITTEST', new_question, length)

        new_header_data = json.loads(new_data)

        # -- if the question does not want the connection to be kept alive, we should not expect it here.
        assert 'Connection' not in new_header_data

        assert new_header_data['Content-Length'] is len(json.dumps(new_question.payload))
        assert new_header_data['Accept-Encoding'] == 'text/json'

    # ------------------------------------------------------------------------------------------------------------------
    def test_decode_response_header(self):
        handler = self.create_handler()
        header = json.dumps(self.example_header_data(), sort_keys=True)
        data = handler.decode_response_header('unittest', header)
        assert data == self.example_header_data()

    # ------------------------------------------------------------------------------------------------------------------
    def test_encode_response_header(self):
        handler = self.create_handler()

        question = clacks.package.Question(
            header_data=self.example_header_data(),
            command='FOO'
        )

        response = clacks.package.Response(
            header_data=self.example_header_data(),
            response=None,
            code=0
        )

        length = handler.get_content_length('', question)

        try:
            handler.encode_response_header(
                'UNITTEST',
                question,
                length
            )

            self.fail()

        except ValueError:
            pass

        length = handler.get_content_length('', response)

        data = handler.encode_response_header(
            'UNITTEST',
            response,
            length
        )

        header_data = json.loads(data)

        assert header_data['Content-Length'] == len(json.dumps(response.payload))
        assert header_data['Connection'] == 'keep-alive'
        assert header_data['Accept-Encoding'] == 'text/json'
