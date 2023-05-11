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
from .base import ServerAdapterBase
from ..errors.codes import ReturnCodes
from .constants import register_adapter_type


# ------------------------------------------------------------------------------------------------------------------
class DeprecationWarningsAdapter(ServerAdapterBase):

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_digest(self, server, handler, connection, transaction_id, header_data, data, response):
        key = data.get('command')

        command = server.get_command(key)

        if not command:
            return

        # -- if the command is deprecated, log a warning and set the return code if it's OK - if it's not, leave it.
        if key in command.former_aliases:
            if response.code is ReturnCodes.OK:
                response.code = ReturnCodes.DEPRECATED

            warning = f'Warning! Command {key} has been deprecated. Please upgrade any API calls to one of its current ' \
                      f'aliases: {command.aliases}.'

            server.logger.warning(warning)

            response.warnings.append(warning)


register_adapter_type('deprecation_warnings', DeprecationWarningsAdapter)
