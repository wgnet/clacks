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
from ...command import aka
from ..base import ServerInterface
from ..constants import register_server_interface_type


# ----------------------------------------------------------------------------------------------------------------------
class StandardServerInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def get_handler_addresses(self):
        """
        From the server, get a simple list of handler addresses. This is convenient if you just want to get the combo
        of host, port, rather than the handler instance itself.

        :return: list of addresses in format Tuple(host, port)
        :rtype: list
        """
        return list(self.server.handler_addresses.values())

    # ------------------------------------------------------------------------------------------------------------------
    def list_commands(self):
        # type: () -> list
        """
        List all commands on this server.

        :return: A sorted list of commands available on this server.
        :rtype: list
        """
        result = [
            cmd
            for cmd in self.server.commands.keys()
            if self.server.commands[cmd].get('private') is False
        ]
        return sorted(list(result))

    # ------------------------------------------------------------------------------------------------------------------
    def disconnect_client(self, address):
        # type: (tuple) -> bool
        """
        Disconnect the given client from this server.

        :param address: tuple of (host, socket) to disconnect.
        :type address: tuple

        :return: True if successful
        :rtype: bool
        """
        return self.server._disconnect_client(address=address)

    # ------------------------------------------------------------------------------------------------------------------
    def shutdown(self):
        """
        Shut down the server.

        :return: None
        :rtype: None
        """
        self.server.logger.warning('Shutting down server %s' % self.server)
        self.server.end()

    # ------------------------------------------------------------------------------------------------------------------
    def command_exists(self, command):
        """
        Returns True if the given command exists on this server. This includes all registered interfaces.

        :param command: The command name to check
        :type command: str

        :return: True if the command exists
        :rtype: bool
        """
        # type: (str) -> bool
        cmd = self.server.get_command(command)
        if cmd is None:
            return False
        return True

    # ------------------------------------------------------------------------------------------------------------------
    @aka(['interfaces'])
    def implemented_interfaces(self):
        # type: () -> list
        """
        Return all implemented interfaces on this server. Used for proxy construction, automatically assigning
        any proxy equivalents to the proxy server representing this server.

        :return: the list of interface types this server implements.
        :rtype: list
        """
        return sorted(list(self.server.interfaces.keys()))

    # ------------------------------------------------------------------------------------------------------------------
    @aka(['implements'])
    def implements_interface(self, interface_type):
        # type: (str) -> bool
        """
        Return True if this server implements the given interface type.

        :param interface_type: the type of the interface to check if this server implements.
        :type interface_type: str

        :return: True if the given interface is implemented
        :rtype:
        """
        if not isinstance(interface_type, str):
            try:
                interface_type = str(interface_type)
            except UnicodeEncodeError:
                pass

        if not isinstance(interface_type, (str, bytes)):
            raise TypeError('interface_type must be a string, got %s!' % type(interface_type))

        for interface in self.server.interfaces:
            if interface.key == interface_type:
                return True

        return False


register_server_interface_type('standard', StandardServerInterface)
