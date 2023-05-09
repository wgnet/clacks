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
