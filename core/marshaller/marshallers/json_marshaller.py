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
import traceback

from clacks.core.package import Package
from clacks.core.marshaller import BasePackageMarshaller
from clacks.core.marshaller import register_marshaller_type


# ----------------------------------------------------------------------------------------------------------------------
class JSONMarshaller(BasePackageMarshaller):

    # ------------------------------------------------------------------------------------------------------------------
    def _encode_package(self, transaction_id, package):
        # type: (str, Package) -> bytes
        data = json.dumps(package.payload, sort_keys=True)
        return bytes(data, encoding=self.encoding)

    # ------------------------------------------------------------------------------------------------------------------
    def _decode_package(self, transaction_id, header_data, payload):
        # type: (str, dict, bytes) -> dict
        result = None
        try:
            payload = payload.decode(self.encoding).lstrip("'").rstrip("'")
            result = json.loads(payload)
        except ValueError:
            self.logger.exception('Could not decode payload {}'.format(payload))
            self.logger.exception(traceback.format_exc())
        return result


register_marshaller_type('json', JSONMarshaller)
