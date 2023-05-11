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
import socket
import typing

from ..handler import BaseRequestHandler
from ..package import Package, Response


# ----------------------------------------------------------------------------------------------------------------------
class ServerAdapterBase(object):

    REQUIRED_INTERFACES = []

    REQUIRED_ADAPTERS = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        self.parent = None

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        return self.__class__.__name__

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self, parent):
        """
        This method is called just before the server is started - this gives handlers, adapters and interfaces the
        opportunity to do some last-minute changes and resource gathering.

        :return: True if successful, if False, the server will not be started.
        :rtype: bool
        """
        self.parent = parent
        return True

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_digest(self, server, handler, connection, transaction_id, header_data, data):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_digest(self, server, handler, connection, transaction_id, header_data, data, response):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_add_to_queue(self, server, handler, connection, transaction_id, header_data, data):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_remove_from_queue(self, server, handler, connection, transaction_id, header_data, data):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_receive_header(self, server, handler, transaction_id):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_receive_header(self, server, handler, transaction_id, header_data):
        """
        This method is invoked after header data has been received by the handler, and is expected to return the header
        data again, acting like a filter. This presents the opportunity for adapters to change incoming header data.
        This can be used to ensure package origin, for purposes like signing, or to trace transactions and their headers
        for profiling and debugging.
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_receive_content(self, server, handler, transaction_id, header_data):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_receive_content(self, server, handler, transaction_id, header_data, content_data):
        """
        This method is invoked after content data has been received by the handler, is expected to return the content
        data again, acting like a filter.
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_compile_buffer(self, server, handler, transaction_id, package):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_compile_buffer(self, server, handler, transaction_id, package):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_respond(self, server, handler, connection, transaction_id, package):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_respond(self, server, handler, connection, transaction_id, package):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_pre_encode_package(self, server, handler, marshaller, transaction_id, package):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_post_encode_package(self, server, handler, marshaller, transaction_id, byte_buffer):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_pre_decode_package(self, server, handler, marshaller, transaction_id, header_data, payload):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def marshaller_post_decode_package(self, server, handler, marshaller, transaction_id, byte_buffer):
        pass
