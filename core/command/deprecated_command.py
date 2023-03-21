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
from .command import ServerCommand
from ..errors import ReturnCodes
from ..package import Question, Response


# ----------------------------------------------------------------------------------------------------------------------
class DeprecatedServerCommand(ServerCommand):

    # ------------------------------------------------------------------------------------------------------------------
    def digest(self, question):
        # type: (Question) -> Response
        response = ServerCommand.digest(self, question)

        # -- deprecated server commands inject a warning in the payload.
        response.warnings.append(
            'Deprecation warning - server command alias %s if marked as deprecated. '
            'Please upgrade any calls to it to one of the following aliases: %s' % (
                question.command,
                self.aliases
            )
        )

        if response.code is ReturnCodes.OK:
            response.code = ReturnCodes.DEPRECATED

        return response

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def from_command(cls, command):
        # type: (ServerCommand) -> DeprecatedServerCommand
        return DeprecatedServerCommand(
            command.interface,
            command._callable,
            private=command.private,
            arg_defaults=command.arg_defaults,
            arg_types=command.arg_types,
            return_type=command.return_type,
            help_obj=command.help_obj,
            aliases=command.former_aliases,
            arg_processors=command.arg_processors,
            result_processors=command.result_processors,
            returns_status_code=command.returns_status_code
        )
