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
import inspect

from ...log import get_logger
from ...utils import is_key_legal

# -- ensure all internal loggers inherit from the root clacks logger
arg_processor_registry_logger = get_logger('arg_processor_registry')

# -- this type of registry implementation follows the standard set by RPyC
arg_processor_registry = {}


# ----------------------------------------------------------------------------------------------------------------------
def validate_function_signature(fn):
    if not callable(fn):
        raise TypeError('Only callable objects with a recognizable function signature can be registered as processors!')

    if hasattr(fn, '_callable'):
        spec = inspect.getargspec(fn._callable)
    else:
        spec = inspect.getargspec(fn)

    if not spec:
        raise ValueError('Could not extract function signature from object %s!' % fn)

    specargs, varargs, varkw, defaults = spec

    if not specargs:
        raise ValueError('Could not extract any positional arguments from function signature of function %s!' % fn)

    if specargs[0] == 'self':
        specargs.pop(0)

    msg = (
        'Argument processor signatures must follow the following pattern: '
        'def fn(server_command, *args, **kwargs).\n'
        'Signature found in function %s: %s' % (fn, specargs)
    )

    if len(specargs) > 1:
        raise ValueError(msg)

    if varargs is None or varkw is None:
        raise ValueError(msg)


# ----------------------------------------------------------------------------------------------------------------------
def register_arg_processor(key, fn, override=False):
    # type: (str, callable, bool) -> None
    global arg_processor_registry

    validate_function_signature(fn)

    if not is_key_legal(key):
        raise KeyError('Invalid key supplied: %s. Please only provide alphanumeric characters (no whitespace)' % key)

    if key in arg_processor_registry:
        if not override:
            raise KeyError('Error type key %s is already registered!' % key)

        arg_processor_registry_logger.warning(
            'Error type %s already registered! Overriding entry with %s' % (key, str(fn))
        )

    arg_processor_registry_logger.debug(
        'Error type %s registered under key %s' % (str(fn), key)
    )

    arg_processor_registry[key] = fn


# ----------------------------------------------------------------------------------------------------------------------
def arg_processor_from_key(key):
    # type: (str) -> callable
    if key not in arg_processor_registry:
        raise KeyError(key)
    return arg_processor_registry[key]


# ----------------------------------------------------------------------------------------------------------------------
def key_from_arg_processor(fn):
    for key, value in arg_processor_registry.items():
        if value != fn:
            continue
        return key
    raise ValueError(fn)
