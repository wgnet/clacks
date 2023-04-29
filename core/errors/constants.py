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

from .codes import ReturnCodes
from ..log import get_logger
from ..utils import is_key_legal

# -- ensure all internal loggers inherit from the root clacks logger
error_registry_logger = get_logger('error_registry')

# -- this type of registry implementation follows the standard set by RPyC
error_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_error_type(key, error_type, override=False):
    # type: (str, type, bool) -> None
    global error_registry

    if not is_key_legal(key):
        raise KeyError('Invalid key supplied: %s. Please only provide alphanumeric characters (no whitespace)' % key)

    if not issubclass(error_type, Exception):
        raise TypeError('Errors must inherit from Exception!')

    if key in error_registry:
        if not override:
            raise KeyError('Error type key %s is already registered!' % key)

        error_registry_logger.warning(
            'Error type %s already registered! Overriding entry with %s' % (key, error_type.__name__)
        )

    error_registry_logger.debug(
        'Error type %s registered under key %s' % (error_type.__name__, key)
    )

    error_registry[key] = error_type


# ----------------------------------------------------------------------------------------------------------------------
def error_from_key(key):
    # type: (str) -> type
    return error_registry.get(key) or Exception


# ----------------------------------------------------------------------------------------------------------------------
def key_from_error_type(error_type):
    # type: (type) -> str
    if isinstance(error_type, type):
        for key, value in error_registry.items():
            if value != error_type:
                continue
            return key
    else:
        for key, value in error_registry.items():
            if not isinstance(error_type, value):
                continue
            return key

    raise KeyError


# ----------------------------------------------------------------------------------------------------------------------
def error_code_from_error(error):
    # type: (typing.Union[type, object]) -> int
    if hasattr(error, 'code'):
        return error.code
    return ReturnCodes.UNHANDLED_EXCEPTION


# ----------------------------------------------------------------------------------------------------------------------
def error_code_from_error_key(key):
    # type: (str) -> int
    error_type = error_from_key(key)
    return error_code_from_error(error_type)


# -- default values that are registered up front
__defaults = {
    'type_error': TypeError,
    'socket_error': socket.error,
    'key_error': KeyError,
    'value_error': ValueError,
    'attribute_error': AttributeError,
    'not_implemented': NotImplementedError,
}


# -- register default error types.
for k, v in __defaults.items():
    register_error_type(k, v)
