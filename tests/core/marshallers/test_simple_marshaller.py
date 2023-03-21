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
class TestSimpleMarshaller(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def question(cls):
        return clacks.package.Question(
            header_data=dict(),
            command='foo',
            **{'test': 'value', 'integer': 0, 'float': 0.2}
        )

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def response(cls, value):
        return clacks.package.Response(
            header_data=dict(),
            response=value,
            code=0
        )

    # ------------------------------------------------------------------------------------------------------------------
    def test__encode_package(self):
        marshaller = clacks.marshaller.SimplePackageMarshaller()
        marshaller._encode_package('UNITTEST', self.question())

        for value in [
            'string',
            0.2,
            1,
            ['list'],
            {'type': 'dict'},
            None,
        ]:
            marshaller._encode_package('UNITTEST', self.response(value))

    # ------------------------------------------------------------------------------------------------------------------
    def test__decode_package(self):
        marshaller = clacks.marshaller.SimplePackageMarshaller()
        response = marshaller._encode_package('UNITTEST', self.question())
        data = marshaller._decode_package('UNITTEST', dict(), response)
        assert data['command'] == 'foo'
        assert data['kwargs'] == {u'test': u'value', u'integer': 0, u'float': 0.2}

        for value in [
            'string',
            0.2,
            1,
            ['list'],
            {'type': 'dict'},
            None,
        ]:
            response = marshaller._encode_package('UNITTEST', self.response(value))
            data = marshaller._decode_package('UNITTEST', dict(), response)
            assert data['response'] == value
