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
from xml.etree import ElementTree as xml

from ...handler import BaseRequestHandler
from ...handler import register_handler_type
from ....core.package import Package, Response


# ----------------------------------------------------------------------------------------------------------------------
class XMLHandler(BaseRequestHandler):

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def dict_to_xml(cls, data):
        root = xml.Element('root')

        for key, value in data.items():
            child = xml.Element(key)
            child.text = str(value)
            root.append(child)

        return root

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def xml_to_dict(cls, xml_data):
        result = collections.OrderedDict()

        root = xml.fromstring(xml_data)

        for child in root:
            result[child.tag] = child.text

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def _get_header_data(self, transaction_id, payload, header_data):
        # type: (str, Package, collections.OrderedDict) -> collections.OrderedDict
        result = collections.OrderedDict()

        result['Content-Length'] = self.get_content_length(transaction_id, payload)
        result['Accept-Encoding'] = 'text/xml'

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
        return self.xml_to_dict(data)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_question_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> bytes
        return xml.tostring(
            self.dict_to_xml(
                self.get_outgoing_header_data(transaction_id, payload, expected_content_length)
            ),
            encoding=self.FORMAT
        )

    # ------------------------------------------------------------------------------------------------------------------
    def decode_response_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        if not isinstance(header, str):
            data = str(header, self.FORMAT)
        else:
            data = str(header)
        return self.xml_to_dict(data)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_response_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Response, int) -> bytes
        return xml.tostring(
            self.dict_to_xml(
                self.get_outgoing_header_data(transaction_id, payload, expected_content_length)
            ),
            encoding=self.FORMAT
        )


register_handler_type('xml', XMLHandler)
