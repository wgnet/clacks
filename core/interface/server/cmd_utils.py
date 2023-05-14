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
from ...command import attrs_from_command, hidden
from ..base import ServerInterface, ServerCommand
from ..constants import register_server_interface_type
from ...errors import ClacksCommandNotFoundError, ClacksCommandIsPrivateError


# ----------------------------------------------------------------------------------------------------------------------
class CommandUtilsServerInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    def get_command_aliases(self, command: str) -> list:
        result = list()

        cmd = self.server.get_command(command)
        if not cmd:
            raise ClacksCommandNotFoundError(f'Command {command} not found!')

        for key, _cmd in self.server.commands.items():
            if key == command:
                continue

            # -- only append keys from commands that fully match.
            if cmd is _cmd:
                result.append(key)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @hidden
    def get_aliases_by_command(self, command: ServerCommand) -> list:
        result = list()
        for key, cmd in self.server.commands.items():
            if cmd == command:
                result.append(key)
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def get_command_current_aliases_by_former_alias(self, former_alias: str) -> list:
        cmd = self.get_command_by_former_alias(former_alias)
        if not cmd:
            raise ClacksCommandNotFoundError(f'Command {former_alias} not found!')
        return self.get_aliases_by_command(cmd)

    # ------------------------------------------------------------------------------------------------------------------
    def get_command_former_aliases(self, command: str) -> list:
        cmd = self.server.get_command(command)
        if not cmd:
            raise ClacksCommandNotFoundError(f'Command {command} not found!')
        return cmd.get('former_aliases')

    # ------------------------------------------------------------------------------------------------------------------
    def get_command_by_former_alias(self, former_alias: str) -> ServerCommand | None:
        return self.get_all_commands_by_former_alias().get(former_alias)

    # ------------------------------------------------------------------------------------------------------------------
    def get_all_commands_by_former_alias(self) -> dict:
        result = dict()

        for key, cmd in self.server.commands.items():
            former_aliases = cmd.get('former_aliases')

            if not former_aliases:
                continue

            for alias in former_aliases:
                if alias in result:
                    raise ValueError(
                        f'Conflicting former alias discovered on command {cmd}: another command on this server '
                        f'is also formerly known by this name.'
                    )

                result[alias] = cmd

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @hidden
    def get_command(self, key: str) -> ServerCommand:
        """
        Get a ServerCommand instance by its lookup key. This is the same as the command alias.

        :param key: the key to use to look up the command in question
        :type key: str

        :return: ServerCommand instance registered under this key
        :rtype: ServerCommand
        """
        cmd = self.server.commands.get(key)

        if cmd is not None:
            if cmd.get('private'):
                raise ClacksCommandIsPrivateError(f'Command {key} is marked as private!')

            return cmd

        cmd = self.get_command_by_former_alias(key)

        current_aliases = self.get_command_current_aliases_by_former_alias(key)

        self.logger.warning(
            f'Warning! Command {key} has been deprecated. '
            f'Please upgrade any API calls to one of its current aliases: {current_aliases}'
        )

        if cmd is not None:
            return cmd

        raise ClacksCommandNotFoundError(f'Command {key} could not be found!')

    # ------------------------------------------------------------------------------------------------------------------
    def is_command_deprecated(self, command: str) -> bool:
        return command in self.get_command_former_aliases(command)

    # ------------------------------------------------------------------------------------------------------------------
    def find_command(self, pattern: str, match_case: bool = False, ratio: float = 0.6) -> list:
        """
        If the "fuzzywuzzy" module is installed, use partial string matching to find any commands whose name is similar
        to the given pattern. If not, simply search by sub string.
        """
        try:
            import fuzzywuzzy.fuzz as fuzz

        except ImportError:
            fuzz = None

        if match_case:
            pattern = pattern.lower()

        result = list()
        for cmd in self.server.list_commands():
            if match_case:
                cmd = cmd.lower()

            if fuzz is None:
                if pattern not in cmd:
                    continue
                result.append(pattern)

            elif fuzz is not None:
                # noinspection PyUnresolvedReferences
                if fuzz.partial_ratio(cmd, pattern) > ratio:
                    result.append(pattern)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def get_command_args(self, command: str) -> dict:
        """
        From a given command, get a dictionary of its arguments, where the argument name is the key, and the argument
        type is the value.
        """
        cmd = self.server.get_command(command)
        if cmd is None:
            raise ClacksCommandNotFoundError(f'Command {command} not found!')

        result = dict()
        for arg, typ in cmd.arg_types.items():
            result[arg] = typ.__name__

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def command_help(self, command: str) -> str:
        """
        Build a helpful description of the given registered command, using its registered type hints and defaults, as
        well as its doc string.
        """
        cmd = self.server.get_command(command)

        if cmd is None:
            raise ClacksCommandNotFoundError(f'Command {command} not found!')

        return cmd.help()

    # ------------------------------------------------------------------------------------------------------------------
    def command_info(self, command: str) -> dict:
        """
        Get a dictionary of attributes for the given command for external construction of a ServerCommand instance.
        """
        cmd = self.server.get_command(command)

        if cmd is None:
            raise ClacksCommandNotFoundError(f'Command {command} not found!')

        return attrs_from_command(cmd)


register_server_interface_type('cmd_utils', CommandUtilsServerInterface)
