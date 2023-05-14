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
import inspect

from .command import ServerCommand


# ----------------------------------------------------------------------------------------------------------------------
def _serialize(obj):
    if isinstance(obj, typing.Type):
        return _serialize_type(obj)

    if isinstance(obj, dict):
        return _serialize_dict(obj)

    if isinstance(obj, list):
        return _serialize_list(obj)

    return obj


# ----------------------------------------------------------------------------------------------------------------------
def _serialize_type(obj):
    return obj.__name__


# ----------------------------------------------------------------------------------------------------------------------
def _serialize_dict(obj):
    result = dict()

    for key, value in obj.items():
        _key = _serialize(key)
        _value = _serialize(value)
        result[_key] = _value

    return result


# ----------------------------------------------------------------------------------------------------------------------
def _serialize_list(obj):
    result = list()
    for item in obj:
        result.append(_serialize(item))
    return result


# ----------------------------------------------------------------------------------------------------------------------
def attrs_from_command(command: ServerCommand):
    kwargs = dict()

    for attr in dir(command._callable):
        if attr.startswith('_'):
            continue

        value = getattr(command._callable, attr)
        value = _serialize(value)

        kwargs[attr] = value

    return kwargs


# ----------------------------------------------------------------------------------------------------------------------
def is_server_command(function):
    return hasattr(function, 'is_server_command') and getattr(function, 'is_server_command') is True


# ----------------------------------------------------------------------------------------------------------------------
def command_from_callable(interface, function, cls=ServerCommand):
    kwargs = dict()
    kwargs['_callable'] = function
    kwargs['interface'] = interface
    return cls(**kwargs)


# ----------------------------------------------------------------------------------------------------------------------
def get_command_signature(cmd) -> inspect.Signature:
    if hasattr(cmd, '_callable'):
        signature = inspect.signature(cmd._callable)

    else:
        signature = inspect.signature(cmd)

    if not signature:
        raise ValueError(f'Could not extract function signature from object {cmd}!')

    return signature


# ----------------------------------------------------------------------------------------------------------------------
def get_command_return_type(cmd):
    return get_command_signature(cmd).return_annotation


# ----------------------------------------------------------------------------------------------------------------------
def get_command_args(cmd):
    return get_command_signature(cmd).parameters
