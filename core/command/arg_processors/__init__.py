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
from .constants import arg_processor_from_key, key_from_arg_processor, register_arg_processor
from .standard import auto_convert_arguments, enforce_argument_types
from .standard import example_arg_processor, kwargs_from_json
from .utils import auto_strip_args, strip_args
