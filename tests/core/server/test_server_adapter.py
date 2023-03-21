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
from clacks.tests import ClacksTestCase


class TestAdapter(clacks.adapters.ServerAdapterBase):

    def __init__(self):
        super(TestAdapter, self).__init__()
        self.hits = dict(
            server_pre_digest=0,
            server_post_digest=0,
            server_pre_add_to_queue=0,
            server_post_remove_from_queue=0,
            handler_pre_receive_header=0,
            handler_post_receive_header=0,
            handler_pre_receive_content=0,
            handler_post_receive_content=0,
            handler_pre_compile_buffer=0,
            handler_post_compile_buffer=0,
            handler_pre_respond=0,
            handler_post_respond=0,
            marshaller_pre_encode_package=0,
            marshaller_post_encode_package=0,
            marshaller_pre_decode_package=0,
            marshaller_post_decode_package=0,
        )

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def all_points_hit(self):
        print(self.hits)
        return all(self.hits.values())

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_digest(self, handler, connection, transaction_id, header_data, data):
        self.hits['server_pre_digest'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_digest(self, handler, connection, transaction_id, header_data, data, response):
        self.hits['server_post_digest'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_add_to_queue(self, handler, connection, transaction_id, header_data, data):
        self.hits['server_pre_add_to_queue'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_remove_from_queue(self, handler, connection, transaction_id, header_data, data):
        self.hits['server_post_remove_from_queue'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_receive_header(self, transaction_id):
        self.hits['handler_pre_receive_header'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_receive_header(self, transaction_id, header_data):
        self.hits['handler_post_receive_header'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_receive_content(self, transaction_id, header_data):
        self.hits['handler_pre_receive_content'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_receive_content(self, transaction_id, header_data, content_data):
        self.hits['handler_post_receive_content'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_compile_buffer(self, transaction_id, package):
        self.hits['handler_pre_compile_buffer'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_compile_buffer(self, transaction_id, package):
        self.hits['handler_post_compile_buffer'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_respond(self, connection, transaction_id, package):
        self.hits['handler_pre_respond'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_respond(self, connection, transaction_id, package):
        self.hits['handler_post_respond'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_pre_encode_package(self, transaction_id, package):
        self.hits['marshaller_pre_encode_package'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_post_encode_package(self, transaction_id, byte_buffer):
        self.hits['marshaller_post_encode_package'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_pre_decode_package(self, transaction_id, header_data, payload):
        self.hits['marshaller_pre_decode_package'] += 1

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_post_decode_package(self, transaction_id, byte_buffer):
        self.hits['marshaller_post_decode_package'] += 1


# ----------------------------------------------------------------------------------------------------------------------
class TestServerAdapter(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_all_adapter_methods_called(self):
        adapter = TestAdapter()

        self.server.register_adapter('test', adapter)
        self.server.register_adapter('base', clacks.adapters.ServerAdapterBase())

        methods = self.client.list_commands().response
        for method in methods:
            info = self.client.command_info(method)

        assert adapter.all_points_hit is True
