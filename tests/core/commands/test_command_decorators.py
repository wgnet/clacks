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
class TestCommandDecorators(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_returns_status_code(self):
        assert self.client.returns_status_code().response == True
        assert self.client.returns_status_code().code == 666

        cmd = self.server.returns_status_code
        assert cmd.returns_status_code
        assert cmd() == True

    # ------------------------------------------------------------------------------------------------------------------
    def test_returns_status_code_bad(self):
        try:
            self.client.returns_status_code_bad()
            self.fail()
        except clacks.errors.ClacksCommandUnexpectedReturnValueError:
            # -- this is expected to return a ValueError
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_aka(self):
        assert self.client.aka('prince').response == 'prince'
        assert self.client.PRINCE('prince').response == 'prince'

    # ------------------------------------------------------------------------------------------------------------------
    def test_fka(self):
        assert self.client.artist().code == 200
        assert self.client.artist().response is True
        assert self.client.prince().response is True
        assert self.client.prince().code is clacks.errors.codes.ReturnCodes.DEPRECATED
        assert len(self.client.prince().warnings) > 0

    # ------------------------------------------------------------------------------------------------------------------
    def test_takes(self):
        assert len(self.client.takes('first', 2).response) == 2

    # ------------------------------------------------------------------------------------------------------------------
    def test_returns(self):
        assert self.client.returns().response == 'string'

    # ------------------------------------------------------------------------------------------------------------------
    def test_private(self):
        try:
            response = self.client.private_fn()
            self.fail()
        except clacks.errors.ClacksCommandIsPrivateError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_returns_response(self):
        assert self.client.returns_response().code == 667
