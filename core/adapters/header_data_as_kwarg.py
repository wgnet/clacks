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
class HeaderDataAsKwargAdapter(ServerAdapterBase):

    # ------------------------------------------------------------------------------------------------------------------
    def server_pre_digest(self, server, handler, connection, transaction_id, header_data, data):
        command = data.get('command')

        if not command:
            return

        srv_command = server.get_command(command)
        if not srv_command:
            # -- it is not this adapter's job to decide what to do if a command does not exist, so we don't complain
            # -- here!
            return

        # -- do nothing if the incoming command does not return a status code
        if not srv_command.get('takes_header_data', False):
            return

        if 'kwargs' not in data:
            data['kwargs'] = dict()
        data['kwargs']['_header_data'] = header_data


register_adapter_type('header_data_as_kwarg', HeaderDataAsKwargAdapter)
