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
import typing
from ..log import get_logger
from ..utils import is_key_legal


# -- ensure all internal loggers inherit from the root clacks logger
adapter_registry_logger = get_logger('adapter_registry')


# -- this type of registry implementation follows the standard set by RPyC
adapter_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_adapter_type(key, adapter_type, override=False):
    # type: (str, type, bool) -> None
    global adapter_registry

    if not is_key_legal(key):
        raise KeyError('Illegal tokens detected in key %s!' % key)

    from .base import ServerAdapterBase

    if adapter_type is ServerAdapterBase:
        raise ValueError('Cannot register ServerAdapterBase - this is an abstract class!')

    if not issubclass(adapter_type, ServerAdapterBase):
        raise ValueError('All adapters must inherit from ServerAdapterBase!')

    if key in adapter_registry:
        if not override:
            raise KeyError('adapter type %s is already registered!' % key)

        adapter_registry_logger.warning(
            'adapter type %s already registered! Overriding entry with %s' % (key, adapter_type.__name__)
        )

    adapter_registry_logger.debug(
        'adapter type %s registered under key %s' % (adapter_type.__name__, key)
    )
    adapter_registry[key] = adapter_type


# ----------------------------------------------------------------------------------------------------------------------
def adapter_from_key(key):
    # type: (str) -> typing.Type
    if key in adapter_registry:
        return adapter_registry.get(key)
    raise KeyError('adapter type %s is not registered!' % key)
