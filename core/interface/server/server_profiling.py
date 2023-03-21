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
from ..base import ServerInterface
from ..constants import register_server_interface_type
from ...adapters.profiling import ProfilingAdapter
from ...command import returns, takes


# ----------------------------------------------------------------------------------------------------------------------
class ProfilingServerInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(ProfilingServerInterface, self).__init__()
        self.adapter = ProfilingAdapter()

    # ------------------------------------------------------------------------------------------------------------------
    def register(self, server):
        # type: (ServerBase) -> None
        super(ProfilingServerInterface, self).register(server)
        # -- this interface comes with an automatically registered profiling adapter
        self.server.register_adapter('profiling', self.adapter)

    # ------------------------------------------------------------------------------------------------------------------
    @returns(bool)
    def is_profiling_enabled(self):
        # type: () -> bool
        """
        Return whether server command profiling is currently enabled.

        :return: "command profiling enabled" state.
        :rtype: bool
        """
        return self.adapter.enabled

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'enabled': bool})
    @returns(None)
    def set_profiling_enabled(self, enabled):
        # type: (bool) -> None
        """
        Set profiling enabled, adding profiling dumps to every digested command.

        :param enabled: whether to enable profiling.
        :type enabled: true

        :return: None
        """
        self.adapter.enabled = enabled


register_server_interface_type('profiling', ProfilingServerInterface)
