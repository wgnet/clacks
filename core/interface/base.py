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

from ..command import ServerCommand


# ----------------------------------------------------------------------------------------------------------------------
class ServerInterface(object):

    COMMON_ATTRIBUTES = {}

    ONLY_REGISTER_DECORATED_COMMANDS = False

    REQUIRED_INTERFACES = []

    REQUIRED_ADAPTERS = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        self.commands = dict()
        self.server = None

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self):
        # type: () -> bool
        """
        This method is called just before the server is started - this gives handlers, adapters and interfaces the
        opportunity to do some last-minute changes and resource gathering.

        :return: True if successful, if False, the server will not be started.
        :rtype: bool
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        # type: () -> logging.Logger
        return self.server.logger

    # ------------------------------------------------------------------------------------------------------------------
    def register(self, server):
        # type: (ServerBase) -> None
        self.server = server

        for key, command in self.commands.items():
            server.register_command(key=key, _callable=command)

        # -- on interfaces, every command is registered, except commands that start with an underscore, making
        # -- as private or internal.
        for key in dir(self):
            # -- methods starting with underscores are considered internally private to the interface itself and are
            # -- ignored.
            # -- this is different from the "private" flag through decorators which can create methods that can be
            # -- called on the server layer but not by a proxy.
            if key.startswith('_'):
                continue

            # -- do not register this method itself
            if key == 'register':
                continue

            value = getattr(self, key)

            if not value:
                continue

            if not callable(value):
                continue

            # -- if we only want to register decorated commands, then only register those.
            if self.ONLY_REGISTER_DECORATED_COMMANDS:
                if not ServerCommand.is_decorated(value):
                    continue
            
            for attr in self.COMMON_ATTRIBUTES:
                if hasattr(value, attr):
                    val = getattr(value, attr)
                    if isinstance(val, list):
                        setattr(value, attr, val + self.COMMON_ATTRIBUTES[attr])
                    elif isinstance(val, dict):
                        val.update(self.COMMON_ATTRIBUTES[attr])
                    else:
                        setattr(value, attr, self.COMMON_ATTRIBUTES[attr])
                elif not hasattr(value, attr):
                    value.__dict__[attr] = self.COMMON_ATTRIBUTES[attr]

            # -- server interfaces should not register hidden commands
            if hasattr(value, 'hidden') and getattr(value, 'hidden'):
                continue

            # -- Construct a server command, extracting any decorated information that might exist.
            value = ServerCommand.construct(interface=self, function=value)
            server.register_command(key=key, _callable=value)
