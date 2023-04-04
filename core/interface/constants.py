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
from ..log import get_logger
from ..utils import is_key_legal


# -- ensure all internal loggers inherit from the root clacks logger
server_interface_registry_logger = get_logger('server_interface_registry')
proxy_interface_registry_logger = get_logger('proxy_interface_registry')


# -- this type of registry implementation follows the standard set by RPyC
server_interface_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_server_interface_type(key, interface_type, override=False):
    # type: (str, type, bool) -> None
    global server_interface_registry

    if not is_key_legal(key):
        raise KeyError('Illegal tokens detected in key %s!' % key)

    from .base import ServerInterface

    if interface_type is ServerInterface:
        raise ValueError('Cannot register ServerInterface - this is an abstract class!')

    if not issubclass(interface_type, ServerInterface):
        raise ValueError('All server interfaces must inherit from ServerInterface!')

    if key in server_interface_registry:
        if not override:
            raise KeyError('Server Interface type %s is already registered!' % key)

        server_interface_registry_logger.warning(
            'Server Interface type %s already registered! Overriding entry with %s' % (key, interface_type.__name__)
        )

    server_interface_registry_logger.debug(
        'Server Interface type %s registered under key %s' % (interface_type.__name__, key)
    )

    server_interface_registry[key] = interface_type


# ----------------------------------------------------------------------------------------------------------------------
def server_interface_from_type(key):
    # type: (str) -> type
    if server_interface_registry.get(key):
        return server_interface_registry.get(key)
    raise KeyError(f'Server Interface type {key} is not registered!\n'
                   f'Registered interface types: {server_interface_registry.keys()}')


# -- this type of registry implementation follows the standard set by RPyC
proxy_interface_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_proxy_interface_type(key, interface_type, override=False):
    # type: (str, type, bool) -> None
    global proxy_interface_registry

    if not is_key_legal(key):
        raise KeyError('Illegal tokens detected in key %s!' % key)

    from .base import ServerInterface

    if interface_type is ServerInterface:
        raise ValueError('Cannot register ServerInterface - this is an abstract class!')

    if not issubclass(interface_type, ServerInterface):
        raise ValueError('All proxy interfaces must inherit from ServerInterface!')

    if key in server_interface_registry:
        if not override:
            raise KeyError('Proxy Interface type %s is already registered!' % key)

        proxy_interface_registry_logger.warning(
            'Proxy Interface type %s already registered! Overriding entry with %s' % (key, interface_type.__name__)
        )

    proxy_interface_registry_logger.debug(
        'Proxy Interface type %s registered under key %s' % (interface_type.__name__, key)
    )

    proxy_interface_registry[key] = interface_type


# ----------------------------------------------------------------------------------------------------------------------
def proxy_interface_from_type(key):
    # type: (str) -> type
    if proxy_interface_registry.get(key):
        return proxy_interface_registry.get(key)
    raise KeyError('Proxy Interface type %s is not registered!' % key)
