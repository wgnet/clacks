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

from .constants import register_arg_processor


# ----------------------------------------------------------------------------------------------------------------------
def strip_args(server_command, *args, **kwargs):
    return list(), dict()


register_arg_processor('strip_args', strip_args)


# ----------------------------------------------------------------------------------------------------------------------
def auto_strip_args(server_command, *args, **kwargs):
    # type: (callable, list, dict) -> typing.Tuple[list, dict]
    if hasattr(server_command, '_callable'):
        spec = inspect.getargspec(server_command._callable)
    else:
        spec = inspect.getargspec(server_command)

    if not spec:
        return list(), dict()

    specargs, varargs, varkw, defaults = spec

    if not specargs:
        return list(), dict()

    if specargs[0] == 'self':
        specargs.pop(0)

    default_len = len(defaults) if defaults else 0

    _args = args[:len(specargs) - default_len]

    keys = specargs[:]

    _kwargs = dict()
    for key in keys:
        # -- don't duplicate keyword arguments!
        if key in specargs:
            continue
        _kwargs[key] = kwargs.get(key, None)

    return _args, _kwargs


register_arg_processor('auto_strip_args', auto_strip_args)
