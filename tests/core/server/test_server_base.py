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
import time
import clacks
import threading
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class TestServerBase(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_getattr(self):
        try:
            # -- expect this to fail
            value = self.server.foobar
            self.fail()
        except AttributeError:
            pass

        # -- try to get attributes for an interface

        try:
            # -- this is an attribute, not a command
            value = self.server.stream
        except AttributeError:
            self.fail()

        # -- this should not fail
        command = self.server.setup_logging_broadcast
        assert isinstance(command, clacks.ServerCommand)

    # ------------------------------------------------------------------------------------------------------------------
    def test_digest_bad_question(self):
        response = self.server.digest(None, None, None, dict(), dict())
        assert response.traceback is not None
        assert response.code == clacks.ReturnCodes.BAD_QUESTION

    # ------------------------------------------------------------------------------------------------------------------
    def test_digest_bad_command(self):
        response = self.server.digest(None, None, None, header_data=dict(), data=dict(command='foobar'))
        assert response.traceback is not None
        assert response.code == clacks.ReturnCodes.NOT_FOUND

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_command(self):
        try:
            self.server._register_command('key', None)
            self.fail()
        except ValueError:
            pass

        def foo():
            print('bar')

        def bar():
            print('foo')

        # -- register a different command onto the same key - this is purely for coverage and checking
        # -- that the logging mechanism to let the developer know about this works properly.
        try:
            self.server.register_command('foo', foo)
            self.server.register_command('foo', bar)
            self.fail()
        except Exception:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_remove_nonexistent_client(self):
        # -- this should return false
        try:
            self.server.remove_client(None)
            self.fail()
        except ValueError:
            pass

        try:
            self.server._disconnect_client(None)
            self.fail()
        except ValueError:
            pass

        try:
            self.server._disconnect_client(['list', 'of', 'bad', 'length'])
            self.fail()
        except ValueError:
            pass

        try:
            self.server._disconnect_client(('tuple', 'of', 'bad', 'length'))
            self.fail()
        except ValueError:
            pass

        try:
            self.server._disconnect_client(('bad', 'values'))
            self.fail()
        except ValueError:
            pass

        # -- nonexistent address that does however meet all other requirements, and should not raise an exception
        assert self.server._disconnect_client(('localhost', '50')) is False

    # ------------------------------------------------------------------------------------------------------------------
    def test_disconnect_client(self):
        # -- this disconnects the client
        result = self.client.disconnect()
        assert result == True
        assert self.client.connected == False

    # ------------------------------------------------------------------------------------------------------------------
    def test_blocking_server(self):
        # -- this test method is done purely to ensure blocking behaviour works, and to generate more coverage.
        server = clacks.ServerBase('test blocking')

        thread = threading.Thread(target=server.start, kwargs=dict(blocking=True))
        thread.daemon = True
        thread.start()

        time.sleep(1)

        server.end()

    # ------------------------------------------------------------------------------------------------------------------
    def test_crash_client(self):
        # -- intentionally set all connections to not blocking, with a super short timeout and lifetime.
        # -- this will artificially raise a timeout error, simulating a real one
        self.server.clients[0].connection.setblocking(False)
        self.server.clients[0].connection.settimeout(0.1)
        self.server.clients[0].handler.CONNECTION_LIFETIME = 0.1

        self.client.socket.setblocking(False)
        self.client.socket.settimeout(0.1)

        def wait():
            assert len(self.server.clients) == 1
            time.sleep(1)
            assert len(self.server.clients) == 0

        thread = threading.Thread(target=wait)
        thread.start()

        thread.join()

    # ------------------------------------------------------------------------------------------------------------------
    def test_crash_client_address(self):
        assert len(self.server.socket_addresses) == 1
        list(self.server.sockets.keys())[0].close()
        assert len(self.server.socket_addresses) == 0

    # ------------------------------------------------------------------------------------------------------------------
    def test_crash_server(self):
        def crash_server():
            raise Exception

        self.server.register_command('crash_server', crash_server)

        try:
            self.client.crash_server()
            self.fail()

        except Exception:
            pass
