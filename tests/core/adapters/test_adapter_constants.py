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
from clacks import register_adapter_type, adapter_from_key


# ----------------------------------------------------------------------------------------------------------------------
class TestAdapterConstants(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_request_bad_adapter(self):
        try:
            adapter_from_key('foobar')
            self.fail()
        except KeyError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_override_adapter(self):
        class TestAdapter(clacks.ServerAdapterBase):
            pass

        register_adapter_type('test', TestAdapter)

        try:
            register_adapter_type('test', TestAdapter, override=False)
            self.fail()
        except KeyError:
            pass

        try:
            register_adapter_type('test', TestAdapter, override=True)
        except:
            self.fail()

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_adapter(self):
        class FooBar():
            pass

        try:
            register_adapter_type('foobar', FooBar)
            self.fail()
        except ValueError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_base_adapter_type(self):
        from clacks import ServerAdapterBase
        try:
            register_adapter_type('NormalKey', ServerAdapterBase)
            self.fail()
        except ValueError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_adapter_registry_legal_key(self):
        from clacks.core.adapters.gnutp import GNUTerryPratchettHeaderAdapter
        try:
            register_adapter_type('bad key', GNUTerryPratchettHeaderAdapter)
            self.fail()
        except KeyError:
            pass
