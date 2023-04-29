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
import collections

from ...marshaller.base import BasePackageMarshaller
from ...marshaller.constants import register_marshaller_type
from ...package import Package

# -- python 3 does not have "unicode", but it does have "bytes".
_unicode = bytes


# ----------------------------------------------------------------------------------------------------------------------
def decode_package(payload, encoding):
    # type: (bytes, str) -> dict
    data = str(payload.decode(encoding))

    result = dict()

    for line in data.splitlines():
        line = line.strip('\n')
        if not line:
            continue

        value_type, key, value = line.split('/')

        # -- to account for the potential presence of forward slashes in the right-most package component,
        # -- we encode values to hexadecimal.
        value = bytearray.fromhex(value).decode(encoding='utf-8')

        if value_type in ['dict', 'collections.OrderedDict']:
            value = json.loads(value)

        elif value_type == 'None':
            value = None

        elif value_type == 'str':
            value = str(value)

        elif value_type in ['list', 'tuple']:
            value = json.loads(value)
            value = eval(value_type)(value)

        else:
            value = eval(value_type)(value)

        result[str(key)] = value

    return result


# ----------------------------------------------------------------------------------------------------------------------
def encode_package(data, encoding):
    # type: (dict, str) -> bytes
    result = ''

    def _encode(val):
        # -- sanitize input
        _val = bytes(str(val), encoding='utf-8').hex()
        return _val

    for key, value in data.items():
        if isinstance(value, (dict, collections.OrderedDict)):
            try:
                _value = json.dumps(value, sort_keys=True)
            except:
                raise ValueError('Could not JSON dump string {json_string}.\nException:{tb}'.format(
                    json_string=value, tb=traceback.format_exc())
                )
            result += 'dict/%s/%s\n' % (key, _encode(_value))

        elif value is None:
            result += 'None/%s/%s\n' % (key, _encode(value))

        elif isinstance(value, (str, bytes, _unicode)):
            result += 'str/%s/%s\n' % (key, _encode(str(value)))

        elif isinstance(value, (list, tuple)):
            result += '%s/%s/%s\n' % (value.__class__.__name__, key, _encode(json.dumps(value, sort_keys=True)))

        elif isinstance(value, bool):
            result += 'bool/%s/%s\n' % (key, _encode(str(value)))

        elif isinstance(value, int):
            result += 'int/%s/%s\n' % (key, _encode(str(value)))

        elif isinstance(value, float):
            result += 'float/%s/%s\n' % (key, _encode(str(value)))

        else:
            raise TypeError(f'Could not encode class type {value.__class__.__name__}')

    return bytes(result, encoding)


# ----------------------------------------------------------------------------------------------------------------------
class SimplePackageMarshaller(BasePackageMarshaller):

    def _encode_package(self, transaction_id, package):  # type: (str, Package) -> bytes
        return encode_package(package.payload, self.encoding)

    def _decode_package(self, transaction_id, header_data, payload):  # type: (str, dict, bytes) -> dict
        return decode_package(payload, self.encoding)


register_marshaller_type('simple', SimplePackageMarshaller)
