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
from ..utils import get_command_args


# ----------------------------------------------------------------------------------------------------------------------
def kwargs_from_json(fn):
    """
    Argument processor to take its keyword arguments from JSON data.

    This processor does not support _actual_ keyword arguments, and will assume that the JSON data from which we take
    our keyword arguments will come from the first element in the positional argument list.

    The assumption being made, therefore, is that there are no keyword arguments, and only 1 positional argument of
    type string, which is expected to be JSON compliant.
    """
    def wrapper(*args, **kwargs):
        if len(kwargs.keys()) != 0:
            raise ValueError('kwargs from json takes 0 kwargs, got %s: %s' % (len(kwargs.keys()), kwargs))

        if not len(args) == 1:
            raise ValueError('kwargs from json only takes 1 argument, got %s: %s' % (len(args), args))

        json_data = args[0]

        try:
            new_kwargs = json.loads(json_data)
        except:
            raise ValueError('Json data failed to load! Received data: %s' % json_data)

        _args = list()

        # -- positionals here are ignored, only the json data is considered.
        return fn(*_args, **new_kwargs)

    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
def enforce_type_annotation(fn):
    parameters = get_command_args(fn)
    param_keys = list(parameters.keys())

    def wrapper(*args, **kwargs):
        errors = list()

        # -- iterate over positionals
        for i in range(len(args)):
            param = parameters[param_keys[i]]
            value = args[i]

            # -- if the parameter is not annotated, don't validate.
            if not param.annotation:
                continue

            if not isinstance(value, param.annotation):
                errors.append(
                    f'Positional argument {param} was given type {type(value)} but expected {param.annotation}!'
                )

        # -- this might throw a KeyError if an incorrect argument is provided
        for key, value in kwargs.items():
            param = parameters[key]
            value = kwargs[key]

            # -- if the parameter is not annotated, don't validate.
            if not param.annotation:
                continue

            if not isinstance(value, param.annotation):
                errors.append(
                    f'Positional argument {param} was given type {type(value)} but expected {param.annotation}!'
                )

        if len(errors):
            raise TypeError('\n'.join(errors))

        return fn(*args, **kwargs)

    return wrapper
