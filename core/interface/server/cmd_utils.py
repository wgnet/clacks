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
from ...command import process_arguments, returns, returns_status_code, takes
from ...command import attrs_from_command
from ...errors.codes import ReturnCodes


# ----------------------------------------------------------------------------------------------------------------------
class CommandUtilsServerInterface(ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'pattern': str, 'match_case': bool, 'ratio': float})
    @returns(list)
    @process_arguments(['auto_strip_args'])
    def find_command(self, pattern, match_case=False, ratio=0.6):
        """
        If the "fuzzywuzzy" module is installed, use partial string matching to find any commands whose name is similar
        to the given pattern. If not, simply search by sub string.

        :param pattern: pattern to match.
        :type pattern: str

        :param match_case: if True, the search is case-sensitive.
        :type match_case: bool

        :param ratio: if the "fuzzywuzzy" module is installed, this value will be used to compare to the partial_ratio.
        :type ratio: float

        :return: list of command names matching the pattern.
        :rtype: list
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

            else:
                if fuzz.partial_ratio(cmd, pattern) > ratio:
                    result.append(pattern)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    @returns(str)
    @process_arguments(['auto_strip_args'])
    def get_command_args(self, command):
        """
        From a given command, get a dictionary of its arguments, where the argument name is the key, and the argument
        type is the value.

        :param command: The command from which to get the arguments
        :type command: str

        :return: A dictionary of (arg_name, arg_type)
        :rtype: dict
        """
        cmd = self.server.get_command(command)
        if cmd is None:
            return 'Command {command} not found!'.format(command=command)

        result = dict()
        for arg, typ in cmd.arg_types.items():
            result[arg] = typ.__name__

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    @returns(tuple)
    @returns_status_code
    @process_arguments(['auto_strip_args'])
    def command_help(self, command):
        # type: (str) -> tuple
        """
        Build a helpful description of the given registered command, using its registered type hints and defaults, as
        well as its doc string.

        :param command: the lookup key of the command in question
        :type command: str

        :return: the help string for the given command
        :rtype: str
        """
        cmd = self.server.get_command(command)

        if cmd is None:
            return None, ReturnCodes.NOT_FOUND

        return cmd.help(), ReturnCodes.OK

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'command': str})
    @returns(tuple)
    @returns_status_code
    @process_arguments(['auto_strip_args'])
    def command_info(self, command):
        # type: (str) -> tuple
        """
        Get a dictionary of attributes for the given command for external construction of a ServerCommand instance.

        :param command: the lookup key of the command in question
        :type command: str

        :return: the information about the given command
        :rtype: str
        """
        cmd = self.server.get_command(command)

        if cmd is None:
            return None, ReturnCodes.NOT_FOUND

        return attrs_from_command(cmd), ReturnCodes.OK


register_server_interface_type('cmd_utils', CommandUtilsServerInterface)
