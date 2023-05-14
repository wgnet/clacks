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
from .constants import register_adapter_type


# ----------------------------------------------------------------------------------------------------------------------
class ClacksStatusCodeAdapter(ServerAdapterBase):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(ClacksStatusCodeAdapter, self).__init__()
        self.transaction_cache = dict()

    # ------------------------------------------------------------------------------------------------------------------
    def server_post_digest(self, server, handler, connection, transaction_id, header_data, data, response):
        command = data.get('command')

        srv_command = server.get_command(command)
        if not srv_command:
            # -- it is not this adapter's job to decide what to do if a command does not exist, so we don't complain
            # -- here!
            return

        # -- do nothing if the incoming command does not return a status code
        if not srv_command.get('returns_status_code', False):
            return

        if not isinstance(response.response, tuple):
            raise TypeError(f'Command {command} did not return a tuple result with a status code!')

        if not isinstance(response.response[1], int):
            raise TypeError(f'Command {command} did not return an integer as its status code!')

        value, code = response.response

        # -- transmute our response
        response.response = value
        response.code = code


register_adapter_type('status_code', ClacksStatusCodeAdapter)
