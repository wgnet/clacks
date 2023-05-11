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
import typing

from .command import ServerCommand
from .arg_processors import arg_processor_from_key, key_from_arg_processor
from .result_processors import result_processor_from_key, key_from_result_processor


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

        if attr == 'arg_processors':
            _value = list()
            for item in value:
                if callable(item):
                    _value.append(key_from_arg_processor(item))
                else:
                    _value.append(item)
            value = _value

        elif attr == 'result_processors':
            _value = list()
            for item in value:
                if callable(item):
                    _value.append(key_from_result_processor(item))
                else:
                    _value.append(item)
            value = _value

        else:
            value = _serialize(value)

        kwargs[attr] = value

    return kwargs


# ----------------------------------------------------------------------------------------------------------------------
def is_server_command(function):
    return hasattr(function, 'is_server_command') and getattr(function, 'is_server_command') is True


# ----------------------------------------------------------------------------------------------------------------------
def command_from_callable(interface, function, cls=ServerCommand):
    attrs = [
        'return_type',
        'arg_types',
        'aliases',
        'returns_status_code',
        'private',
        'former_aliases',
    ]

    kwargs = dict()

    for key in attrs:
        if not hasattr(function, key):
            continue
        kwargs[key] = getattr(function, key)

    arg_types = kwargs.get('arg_types', None)

    # -- this is relevant for server command instances that are transferred as JSON objects.
    # -- this basically allows us to serialize a command and construct a proxy of it on a remote server
    # -- automatically.
    if arg_types:
        converted = dict()
        for key, value in kwargs['arg_types'].items():
            if not isinstance(value, (str, bytes)):
                converted[key] = value
            else:
                converted[key] = eval(value)
        kwargs['arg_types'] = converted

    if 'return_type' in kwargs:
        if not isinstance(kwargs['return_type'], (str, bytes)):
            kwargs['return_type'] = kwargs['return_type']
        else:
            kwargs['return_type'] = eval(kwargs['return_type'])

    if hasattr(function, 'arg_processors'):
        processors = function.arg_processors

        _processors = list()
        for proc in processors:
            if callable(proc):
                _processors.append(proc)
            elif isinstance(proc, (str, bytes)):
                _processors.append(arg_processor_from_key(proc))

        kwargs['arg_processors'] = _processors

    if hasattr(function, 'result_processors'):
        processors = function.result_processors

        _processors = list()
        for proc in processors:
            if callable(proc):
                _processors.append(proc)
            elif isinstance(proc, (str, bytes)):
                _processors.append(result_processor_from_key(proc))

        kwargs['result_processors'] = _processors

    kwargs['_callable'] = function
    kwargs['interface'] = interface

    return cls(**kwargs)


# ----------------------------------------------------------------------------------------------------------------------
def get_command_args(cmd):
    if not callable(cmd):
        raise TypeError('Only callable objects with a recognizable function signature can be registered as processors!')

    if hasattr(cmd, '_callable'):
        spec = inspect.signature(cmd._callable)
    else:
        spec = inspect.signature(cmd)

    if not spec:
        raise ValueError('Could not extract function signature from object %s!' % cmd)

    return spec.parameters
