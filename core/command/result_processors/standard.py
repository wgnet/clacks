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

from .constants import register_result_processor
from ..command import ServerCommand


# ----------------------------------------------------------------------------------------------------------------------
def example_result_processor(server_command, result):
    # type: (ServerCommand, object) -> object
    """
    Example result processor, is expected to return the the processed result.
    A practical use case would be to marshal the return data to a JSON string, allowing a given interface's methods
    to be written
    """
    return result


register_result_processor('example_result_processor', example_result_processor)


# ----------------------------------------------------------------------------------------------------------------------
def enforce_return_type(server_command, result):
    # type: (ServerCommand, object) -> object
    return_type = server_command.return_type
    if not isinstance(result, return_type):
        raise TypeError('Return type expected %s, got %s!' % (return_type, type(result)))
    return result


register_result_processor('enforce_return_type', enforce_return_type)


# ----------------------------------------------------------------------------------------------------------------------
def return_as_json(server_command, result):
    # type: (ServerCommand, object) -> object
    if not isinstance(result, (list, dict)):
        raise ValueError('non JSON compatible data provided!')
    return json.dumps(result, sort_keys=True)


register_result_processor('return_as_json', return_as_json)
