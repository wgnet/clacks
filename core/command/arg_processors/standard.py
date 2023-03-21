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
import typing

from .constants import register_arg_processor
from ..command import ServerCommand


# ----------------------------------------------------------------------------------------------------------------------
def example_arg_processor(server_command, *args, **kwargs):
    # type: (ServerCommand, typing.Union[object, list], typing.Union[object, dict]) -> typing.Tuple[list, dict]
    """
    Example argument processor illustrating the usage.

    Argument processors get:

    - the server command instance calling them
    - an arbitrary positional argument list
    - an arbitrary keyword argument list (as a dictionary)

    Argument processors are expected to return a tuple of:

    - the positional argument list
    - the keyword argument list (as a dictionary)

    :param server_command: the Server Command being processed.
    :type server_command: ServerCommand

    :param args: positional arguments passed through
    :type args: list

    :param kwargs: keyword arguments passed through
    :type kwargs: dict

    :return: tuple of List, Dict, denoting args and kwargs
    :rtype: typing.Tuple[list, dict]
    """
    return args, kwargs


register_arg_processor('example_arg_processor', example_arg_processor)


# ----------------------------------------------------------------------------------------------------------------------
def enforce_argument_types(server_command, *args, **kwargs):
    # type: (ServerCommand, typing.Union[object, list], typing.Union[object, dict]) -> typing.Tuple[list, dict]
    """
    Argument processor that enforces type hints for keyword arguments only, as positionals are not decorated.
    This only works if the given server command contains any actual type hints.

    :param server_command: the Server Command being processed.
    :type server_command: ServerCommand

    :param args: positional arguments passed through
    :type args: list

    :param kwargs: keyword arguments passed through
    :type kwargs: dict

    :return: tuple of List, Dict, denoting args and kwargs
    :rtype: typing.Tuple[list, dict]
    """
    type_hints = getattr(server_command, 'arg_types', dict())
    defaults = getattr(server_command, 'arg_defaults', dict())

    if not type_hints:
        return args, kwargs

    for key in kwargs:
        if key not in type_hints:
            continue

        value = kwargs.get(key) if key in kwargs else defaults.get(key)

        expected = type_hints.get(key)

        if isinstance(value, expected):
            continue

        raise TypeError('Keyword Arg %s expected type %s, got %s!' % (key, expected, type(value)))

    return args, kwargs


register_arg_processor('enforce_argument_types', enforce_argument_types)


# ----------------------------------------------------------------------------------------------------------------------
def kwargs_from_json(server_command, *args, **kwargs):
    # type: (ServerCommand, typing.Union[object, list], typing.Union[object, dict]) -> typing.Tuple[list, dict]
    """
    Argument processor to take its keyword arguments from JSON data.

    This processor does not support _actual_ keyword arguments, and will assume that the JSON data from which we take
    our keyword arguments will come from the first element in the positional argument list.

    The assumption being made, therefore, is that there are no keyword arguments, and only 1 positional argument of
    type string, which is expected to be JSON compliant.

    :param server_command: the Server Command being processed.
    :type server_command: ServerCommand

    :param args: positional arguments passed through
    :type args: list

    :param kwargs: keyword arguments passed through
    :type kwargs: dict

    :return: tuple of List, Dict, denoting args and kwargs
    :rtype: typing.Tuple[list, dict]
    """
    if len(kwargs.keys()) != 0:
        raise ValueError('kwargs from json takes 0 kwargs, got %s: %s' % (len(kwargs.keys()), kwargs))

    if not len(args) == 1:
        raise ValueError('kwargs from json only takes 1 argument, got %s: %s' % (len(args), args))

    json_data = args[0]

    try:
        new_kwargs = json.loads(json_data)
    except:
        raise ValueError('Json data failed to load! Received data: %s' % json_data)

    # -- positionals here are ignored, only the json data is considered.
    return list(), new_kwargs


register_arg_processor('kwargs_from_json', kwargs_from_json)


# ----------------------------------------------------------------------------------------------------------------------
def auto_convert_arguments(server_command, *args, **kwargs):
    # type: (ServerCommand, typing.Union[object, list], typing.Union[object, dict]) -> typing.Tuple[list, dict]
    """
    Argument processor that attempts to automatically convert the arguments it's given to the provided type hints for
    the given ServerCommand. This is particularly useful if the incoming data is serialized to string, but can be
    directly converted back. This is a common scenario for web interfaces, which use strings as a primary interchange
    format.

    :param server_command: the Server Command being processed.
    :type server_command: ServerCommand

    :param args: positional arguments passed through
    :type args: list

    :param kwargs: keyword arguments passed through
    :type kwargs: dict

    :return: tuple of List, Dict, denoting args and kwargs
    :rtype: typing.Tuple[list, dict]
    """
    type_hints = server_command.arg_types
    defaults = getattr(server_command, 'arg_defaults', dict())

    if not type_hints:
        return args, kwargs

    new_kwargs = dict()

    for key in kwargs:
        if key not in type_hints:
            continue

        value = kwargs.get(key) if key in kwargs else defaults.get(key)

        expected = type_hints.get(key)

        # -- convert the argument - this could convert a string to a float for example, useful for web servers.
        if not isinstance(value, expected):
            try:
                new_kwargs[key] = expected(value)
            except Exception:
                raise TypeError('Could not convert %s to type %s!' % (value, expected))

    return args, new_kwargs


register_arg_processor('auto_convert_arguments', auto_convert_arguments)
