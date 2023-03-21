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
__version__ = '1.0.0'

import logging
logging.basicConfig()

from .core import proxy
from .core import errors
from .core import server
from .core import handler
from .core import command
from .core import package
from .core import adapters
from .core import interface
from .core import marshaller
from .core import constants

from .core.utils import get_new_port
from .core.utils import one_off_send
from .core.utils import one_off_receive
from .core.utils import quick_listening_socket

from .core.command import ServerCommand
from .core.command import decorators
from .core.command import arg_processors, result_processors
from .core.command import register_arg_processor, register_result_processor
from .core.command import arg_processor_from_key, key_from_arg_processor
from .core.command import result_processor_from_key, key_from_result_processor

from .core.errors import ReturnCodes
from .core.errors import error_from_key, register_error_type, key_from_error_type

from .core.proxy import acquire_proxy
from .core.proxy import ClientProxyBase

from .core.server import ServerBase
from .core.handler import BaseRequestHandler, SimpleRequestHandler, JSONHandler, XMLHandler
from .core.interface import ServerInterface, register_server_interface_type, register_proxy_interface_type
from .core.marshaller import BasePackageMarshaller, SimplePackageMarshaller, PickleMarshaller, JSONMarshaller
from .core.adapters import ServerAdapterBase, adapter_from_key, register_adapter_type

from .core.package import Question, Response, Package
