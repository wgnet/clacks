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
from ..base import ServerInterface
from ...utils import StreamingSocketReceiver
from ..constants import register_proxy_interface_type


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
    def setup_receiver_stream(self, host: str, port: int, stream: io.FileIO):
        self.stream = StreamingSocketReceiver((host, port), stream)

    # ------------------------------------------------------------------------------------------------------------------
    def setup_logging_broadcast(self, host: str) -> tuple:
        return self.server.question('setup_logging_broadcast', host)


register_proxy_interface_type('logging', ProxyLoggingInterface)
