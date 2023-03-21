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
from .base import BasePackageMarshaller
from ..log import get_logger
from ..utils import is_key_legal

# -- ensure all internal loggers inherit from the root clacks logger
marshaller_registry_logger = get_logger('marshaller_registry')


# -- this type of registry implementation follows the standard set by RPyC
marshaller_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_marshaller_type(key, marshaller_type, override=False):
    # type: (str, type, bool) -> None
    global marshaller_registry

    if not is_key_legal(key):
        raise KeyError('Illegal tokens detected in key %s!' % key)

    if marshaller_type is BasePackageMarshaller:
        raise ValueError('Cannot register ServerInterface - this is an abstract class!')

    if not issubclass(marshaller_type, BasePackageMarshaller):
        raise ValueError('All server interfaces must inherit from ServerInterface!')

    if key in marshaller_registry:
        if not override:
            raise KeyError('Marshaller type %s is already registered!' % key)

        marshaller_registry_logger.warning(
            'Marshaller type %s already registered! Overriding entry with %s' % (key, marshaller_type.__name__)
        )

    marshaller_registry_logger.debug(
        'Marshaller type %s registered under key %s' % (marshaller_type.__name__, key)
    )

    marshaller_registry[key] = marshaller_type


# ----------------------------------------------------------------------------------------------------------------------
def marshaller_from_key(key):
    if key in marshaller_registry:
        return marshaller_registry.get(key)
    raise KeyError('Marshaller type %s is not registered!' % key)
