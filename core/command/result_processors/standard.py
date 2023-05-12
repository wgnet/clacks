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


# ----------------------------------------------------------------------------------------------------------------------
def enforce_return_type(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
def return_as_json(fn):
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        result = json.dumps(result, sort_keys=True)
        return result
    return wrapper
