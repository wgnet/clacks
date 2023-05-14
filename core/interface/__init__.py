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
from . import proxy
from . import server
from .base import ServerInterface
from .constants import proxy_interface_from_type
from .constants import proxy_interface_registry
from .constants import register_proxy_interface_type
from .constants import register_server_interface_type
from .constants import server_interface_from_type
from .constants import server_interface_registry
from .constants import list_available_server_interface_types
