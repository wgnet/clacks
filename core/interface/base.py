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

from ..command import ServerCommand, is_server_command, command_from_callable


# ----------------------------------------------------------------------------------------------------------------------
class ServerInterface(object):

    _COMMAND_CLASS = ServerCommand

    _COMMON_ATTRIBUTES = {}

    _ONLY_REGISTER_DECORATED_COMMANDS = False

    _REQUIRED_INTERFACES = []

    _REQUIRED_ADAPTERS = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        self.parent = None
        self.commands = dict()
        self.server = None

        if not issubclass(self._COMMAND_CLASS, ServerCommand):
            raise TypeError('All server commands must inherit from the base clacks.ServerCommand class!')

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self, parent):
        """
        This method is called just before the server is started - this gives handlers, adapters and interfaces the
        opportunity to do some last-minute changes and resource gathering.

        :return: True if successful, if False, the server will not be started.
        :rtype: bool
        """
        self.parent = parent
        return True

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        # type: () -> logging.Logger
        return self.server.logger

    # ------------------------------------------------------------------------------------------------------------------
    def _can_register_command(self, key):
        # -- methods starting with underscores are considered internally private to the interface itself and are
        # -- ignored.
        # -- this is different from the "private" flag through decorators which can create methods that can be
        # -- called on the server layer but not by a proxy.
        if key.startswith('_'):
            return False

        # -- do not register the register method itself, or our class attributes.
        if key in [
            'register',
        ]:
            return False

        value = getattr(self, key)

        if not value:
            return False

        if not callable(value):
            return False

        # -- if we only want to register decorated commands, then only register those.
        if self._ONLY_REGISTER_DECORATED_COMMANDS:
            if not is_server_command(value):
                return False

        for attr in self._COMMON_ATTRIBUTES:
            if hasattr(value, attr):
                val = getattr(value, attr)

                if isinstance(val, list):
                    setattr(value, attr, val + self._COMMON_ATTRIBUTES[attr])

                elif isinstance(val, dict):
                    val.update(self._COMMON_ATTRIBUTES[attr])
                else:
                    setattr(value, attr, self._COMMON_ATTRIBUTES[attr])

            elif not hasattr(value, attr):
                value.__dict__[attr] = self._COMMON_ATTRIBUTES[attr]

        # -- server interfaces should not register hidden commands
        if hasattr(value, 'hidden') and getattr(value, 'hidden'):
            return False

        return True

    # ------------------------------------------------------------------------------------------------------------------
    def _construct_server_command(self, fn):
        command_class = self._COMMAND_CLASS

        if hasattr(fn, 'command_class'):
            if not issubclass(fn.command_class, ServerCommand):
                raise TypeError(
                    f'Declared command class {fn.command_class} for function {fn} does not inherit '
                    f'from clacks.ServerCommand! All Clacks Server Commands must inherit from this base class.'
                )

            command_class = fn.command_class

        return command_from_callable(interface=self, function=fn, cls=command_class)

    # ------------------------------------------------------------------------------------------------------------------
    def register(self, server):
        # type: (ServerBase) -> None
        self.server = server

        for key, command in self.commands.items():
            server.register_command(key=key, _callable=command)

        # -- on interfaces, every command is registered, except commands that start with an underscore, making
        # -- as private or internal.
        for key in dir(self):
            if not self._can_register_command(key):
                continue

            value = getattr(self, key)

            # -- Construct a server command, extracting any decorated information that might exist.
            value = self._construct_server_command(value)

            if not value:
                continue

            if key not in value.aliases:
                value.aliases.append(key)

            # -- register commands under their key, any of their aliases and any of their former aliases
            keys = value.aliases + value.former_aliases

            for command_key in keys:
                # -- register the command
                server.register_command(key=command_key, _callable=value)
