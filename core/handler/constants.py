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
handler_registry_logger = get_logger('handler_registry')


# -- this type of registry implementation follows the standard set by RPyC
handler_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def register_handler_type(key, handler_type, override=False):
    # type: (str, type, bool) -> None
    global handler_registry

    if not is_key_legal(key):
        raise KeyError('Illegal tokens detected in key %s!' % key)

    from .base import BaseRequestHandler

    if handler_type is BaseRequestHandler:
        raise ValueError('Cannot register BaseRequestHandler - this is an abstract class!')

    if not issubclass(handler_type, BaseRequestHandler):
        raise ValueError('All handlers must inherit from BaseRequestHandler!')

    if key in handler_registry:
        if not override:
            raise KeyError('Handler type %s is already registered!' % key)

        handler_registry_logger.warning(
            'Handler type %s already registered! Overriding entry with %s' % (key, handler_type.__name__)
        )

    handler_registry_logger.debug(
        'Handler type %s registered under key %s' % (handler_type.__name__, key)
    )
    handler_registry[key] = handler_type


# ----------------------------------------------------------------------------------------------------------------------
def handler_from_key(key):
    # type: (str) -> type
    if key in handler_registry:
        return handler_registry.get(key)
    raise KeyError('Handler type %s is not registered!' % key)


# ----------------------------------------------------------------------------------------------------------------------
class HandlerErrors(object):

    BAD_HEADER = 'Bad header. Please provide compatible header. Got %s'
    BAD_CONTENT = 'Bad content. Please provide marshaller-compatible content. Got %s'
