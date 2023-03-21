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
# -- different command types - normal, queued and deprecated.
from .arg_processors import *
from .command import ServerCommand
from .decorators import aka, returns, returns_status_code, takes
from .decorators import fka, private, process_arguments, process_result
from .deprecated_command import DeprecatedServerCommand
from .handler import ServerCommandDigestLoggingHandler
from .queued_command import QueuedServerCommand
from .result_processors import *
