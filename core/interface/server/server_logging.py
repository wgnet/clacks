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
import logging
import sys
import typing

from ..base import ServerInterface
from ..constants import register_server_interface_type
from ...command import returns, takes
from ...utils import StreamingSocket
from ...utils import get_new_port


# ----------------------------------------------------------------------------------------------------------------------
class ServerLoggingInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(ServerLoggingInterface, self).__init__()
        self.stream = None

    # ------------------------------------------------------------------------------------------------------------------
    def __del__(self):
        self.stream.stop()

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'host': str})
    @returns(tuple)
    def setup_logging_broadcast(self, host):
        # type: (str) -> typing.Tuple[str, int]
        port = get_new_port(host)
        self.stream = StreamingSocket(host, port)

        logging.getLogger().setLevel(logging.DEBUG)
        self.server.logger.setLevel(logging.DEBUG)

        sys.stdout = self.stream

        handler = logging.StreamHandler(self.stream)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S'
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(handler)

        return host, port


register_server_interface_type('logging', ServerLoggingInterface)
