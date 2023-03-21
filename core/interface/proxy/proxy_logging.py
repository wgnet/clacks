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
import io
import typing

from ..base import ServerInterface
from ..constants import register_proxy_interface_type
from ...command.decorators import returns, takes
from ...utils import StreamingSocketReceiver


# ----------------------------------------------------------------------------------------------------------------------
class ProxyLoggingInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(ProxyLoggingInterface, self).__init__()
        self.stream = None

    # ------------------------------------------------------------------------------------------------------------------
    def __del__(self):
        if not self.stream:
            return
        self.stream.stop()

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'host': str, 'port': int, 'stream': io.FileIO})
    def setup_receiver_stream(self, host, port, stream):
        self.stream = StreamingSocketReceiver((host, port), stream)

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'host': str})
    @returns(tuple)
    def setup_logging_broadcast(self, host):
        # type: (str) -> typing.Tuple[str, int]
        return self.server.question('setup_logging_broadcast', host)


register_proxy_interface_type('logging', ProxyLoggingInterface)
