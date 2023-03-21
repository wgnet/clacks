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
import cProfile
import pstats
import socket
import sys

from .base import ServerAdapterBase
from .constants import register_adapter_type
from ..handler import BaseRequestHandler
from ..package import Package, Response

# -- python 3 migrates StringIO to io
if sys.version_info.major == 3:
    import io
    _StringIO = io

if sys.version_info.major == 2:
    import StringIO
    _StringIO = StringIO


# ----------------------------------------------------------------------------------------------------------------------
class ProfilingAdapter(ServerAdapterBase):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(ProfilingAdapter, self).__init__()
        # -- this attaches profiling dumps to commands
        self.enabled = False
        self.buffer_compile_profiles = dict()
        self.command_profiles = dict()

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def get_profile_stats(cls, profile):
        # type: (cProfile.Profile) -> str
        profile_buffer = _StringIO.StringIO()
        pstats.Stats(profile, stream=profile_buffer).strip_dirs().sort_stats('cumulative').print_stats()
        result = profile_buffer.getvalue()
        profile_buffer.close()
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_digest(self, handler, connection, transaction_id, header_data, data):
        # type: (BaseRequestHandler, socket.socket, str, dict, dict) -> None
        if not self.enabled:
            return
        profile = cProfile.Profile()
        profile.enable()
        self.command_profiles[transaction_id] = profile

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_digest(self, handler, connection, transaction_id, header_data, data, response):
        # type: (BaseRequestHandler, socket.socket, str, dict, dict, Response) -> None
        if transaction_id not in self.command_profiles:
            return
        self.command_profiles[transaction_id].disable()

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_respond(self, connection, transaction_id, package):
        # type: (socket.socket, str, Package) -> None
        if not self.enabled:
            return

        if 'profiling' not in package.payload:
            package.payload['profiling'] = dict()

        data = dict()

        if transaction_id in self.command_profiles:
            data['command'] = self.get_profile_stats(self.command_profiles[transaction_id])

        if transaction_id in self.buffer_compile_profiles:
            data['buffer_compile'] = self.get_profile_stats(self.buffer_compile_profiles[transaction_id])

        package.payload['profiling'] = data

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_compile_buffer(self, transaction_id, package):
        # type: (str, Package) -> None
        if not self.enabled:
            return
        profile = cProfile.Profile()
        profile.enable()
        self.buffer_compile_profiles[transaction_id] = profile

    # ------------------------------------------------------------------------------------------------------------------
    def handler_post_compile_buffer(self, transaction_id, package):
        # type: (str, Package) -> None
        if not self.enabled:
            return
        self.buffer_compile_profiles[transaction_id].disable()


register_adapter_type('profiling', ProfilingAdapter)
