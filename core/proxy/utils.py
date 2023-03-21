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
from ..handler import handler_from_key
from ..marshaller import marshaller_from_key


proxy_registry = dict()


# ----------------------------------------------------------------------------------------------------------------------
def register_proxy_type(key, proxy_type):
    # type: (str, type) -> None
    global proxy_registry
    proxy_registry[key] = proxy_type


# ----------------------------------------------------------------------------------------------------------------------
def proxy_from_type(proxy_type):
    # type: (str) -> type
    return proxy_registry.get(proxy_type)


# ----------------------------------------------------------------------------------------------------------------------
def acquire_proxy(address, proxy_type, handler_type, marshaller_type):
    handler = handler_from_key(handler_type)

    if handler is None:
        raise ValueError('Could not find handler type %s in registry!' % handler_type)

    marshaller = marshaller_from_key(marshaller_type)

    if marshaller is None:
        raise ValueError('Could not find marshaller type %s in registry!' % marshaller_type)

    proxy = proxy_from_type(proxy_type)

    if proxy is None:
        raise ValueError('Could not find proxy type %s in registry!' % proxy_type)

    proxy = proxy(address, handler(marshaller()))

    return proxy
