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
import clacks
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class TestProfilingAdapter(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_profiling_interface(self):
        server = clacks.ServerBase('unittest profiling interface')
        assert len(server.adapters) == 0
        server.register_interface_by_key('profiling')
        assert len(server.adapters) == 1
        assert isinstance(self.server.adapters[list(self.server.adapters.keys())[0]], clacks.core.adapters.profiling.ProfilingAdapter)

    # ------------------------------------------------------------------------------------------------------------------
    def test_enable_profiling(self):
        self.server.set_profiling_enabled(True)
        assert self.server.adapters[list(self.server.adapters.keys())[0]].enabled
        response = self.client.list_commands()
        assert 'profiling' in response.payload

    # ------------------------------------------------------------------------------------------------------------------
    def test_disable_profiling(self):
        self.server.set_profiling_enabled(False)
        assert self.server.adapters[list(self.server.adapters.keys())[0]].enabled is False
        response = self.client.list_commands()
        assert 'profiling' not in response.payload
