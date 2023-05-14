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
import os
import time
import clacks
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class TestServerLoggingInterface(ClacksTestCase):

    rebuild_server = True

    # ------------------------------------------------------------------------------------------------------------------
    def tearDown(self):
        os.unlink('output.txt')

    # ------------------------------------------------------------------------------------------------------------------
    def test_register(self):
        def foo():
            print('bar')

        self.server.register_command('foo', clacks.command_from_callable(self.interface, foo))

        stream = open('output.txt', 'w+')

        host, port = self.client.setup_logging_broadcast('localhost').response
        self.client.setup_receiver_stream(host, port, stream=stream)

        for i in range(10):
            self.client.foo()

        # -- give the listener a second to catch up
        time.sleep(2)

        stream.close()

        with open('output.txt') as fp:
            value = fp.read()
        fp.close()

        assert value != ''
