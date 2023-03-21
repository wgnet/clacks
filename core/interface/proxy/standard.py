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
from ..constants import register_proxy_interface_type
from ...command import takes


# ----------------------------------------------------------------------------------------------------------------------
class StandardProxyInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def describe(self):
        return self.server.question('describe')

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    def command_help(self, command):
        return self.server.question('command_help', command)

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    def command_info(self, command):
        return self.server.question('command_info', command)

    # ------------------------------------------------------------------------------------------------------------------
    def list_commands(self):
        return self.server.question('list_commands')

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'address': tuple})
    def disconnect_client(self, address):
        self.server.question('disconnect_client', address)

    # ------------------------------------------------------------------------------------------------------------------
    def shutdown(self):
        self.server.question('shutdown')

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    def command_exists(self, command):
        return self.server.question('command_exists', command)

    # ------------------------------------------------------------------------------------------------------------------
    def implemented_interfaces(self):
        return self.server.question('implemented_interfaces')

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'interface_type': str})
    def implements_interface(self, interface_type):
        return self.server.question('implements_interface', interface_type)


register_proxy_interface_type('standard', StandardProxyInterface)
