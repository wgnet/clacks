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


# ------------------------------------------------------------------------------------------------------------------
class GNUTerryPratchettHeaderAdapter(ServerAdapterBase):

    # ------------------------------------------------------------------------------------------------------------------
    def handler_pre_respond(self, server, handler, connection, transaction_id, package):
        if 'header_data' not in package.payload:
            package.payload['header_data'] = dict()
        package.header_data['X-Clacks-Overhead'] = 'GNU Terry Pratchett'


register_adapter_type('gnu', GNUTerryPratchettHeaderAdapter)
