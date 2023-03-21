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
import traceback
from ..package import Package


# ----------------------------------------------------------------------------------------------------------------------
class BasePackageMarshaller(object):

    DEFAULT_RAW_RESPONSE = True

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, encoding='utf-8'):
        self.handler = None
        self.encoding = encoding
        self.adapters = list()

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        return self.handler.server.logger

    # ------------------------------------------------------------------------------------------------------------------
    def register_handler(self, handler):
        self.handler = handler

    # ------------------------------------------------------------------------------------------------------------------
    def raw_response_requested(self, transaction_id):
        return self.transaction_cache(transaction_id).get('raw_response', self.DEFAULT_RAW_RESPONSE)

    # ------------------------------------------------------------------------------------------------------------------
    def transaction_cache(self, transaction_id):
        # type: (str) -> dict
        return self.handler.transaction_cache.get(transaction_id, dict())

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter(self, adapter):
        from ..adapters import ServerAdapterBase

        if not isinstance(adapter, ServerAdapterBase):
            raise ValueError('%s is not a ServerAdapterBase instance!' % adapter)

        self.adapters.append(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def encode_package(self, transaction_id, package):
        # type: (str, Package) -> bytes
        byte_buffer = b''

        try:
            for adapter in self.adapters:
                adapter.marshaller_pre_encode_package(transaction_id, package)

            byte_buffer = self._encode_package(transaction_id, package)

            for adapter in self.adapters:
                adapter.marshaller_post_encode_package(transaction_id, byte_buffer)

        except Exception:
            self.logger.exception(traceback.format_exc())

        return byte_buffer

    # ------------------------------------------------------------------------------------------------------------------
    def decode_package(self, transaction_id, header_data, payload):
        # type: (str, dict, bytes) -> dict
        package = dict()

        try:
            for adapter in self.adapters:
                adapter.marshaller_pre_decode_package(transaction_id, header_data, payload)

            package = self._decode_package(transaction_id, header_data, payload)

            for adapter in self.adapters:
                adapter.marshaller_post_decode_package(transaction_id, package)

        except Exception:
            self.logger.exception(traceback.format_exc())

        return package

    # ------------------------------------------------------------------------------------------------------------------
    def _encode_package(self, transaction_id, package):
        # type: (str, Package) -> bytes
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def _decode_package(self, transaction_id, header_data, payload):
        # type: (str, dict, bytes) -> dict
        raise NotImplementedError
