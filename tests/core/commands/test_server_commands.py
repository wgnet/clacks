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
import unittest


def foo():
    print('bar')


@clacks.decorators.takes({'value': object, 'other': object})
def echo(value=None, other=None):
    return value


# ----------------------------------------------------------------------------------------------------------------------
class TestServerCommands(unittest.TestCase):

    server = None
    client = None

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def get_server_instance():
        server = clacks.ServerBase(identifier='Test Server')
        server.register_interface_by_key('standard')

        handler = clacks.handler.SimpleRequestHandler(clacks.marshaller.SimplePackageMarshaller())
        host, port = 'localhost', clacks.get_new_port('localhost')
        server.register_handler(host, port, handler)

        return server, (host, port)

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def get_client_instance(address):
        client = clacks.ClientProxyBase(
            address,
            handler=clacks.handler.SimpleRequestHandler(clacks.marshaller.SimplePackageMarshaller())
        )
        client.register_interface_by_type('standard')
        return client

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls.server, address = cls.get_server_instance()
        cls.server.start()
        cls.client = cls.get_client_instance(address)

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):
        cls.server.end()

    # ------------------------------------------------------------------------------------------------------------------
    def test_get_doc(self):
        def doc_test():
            """FooBar"""
            return True

        command = clacks.ServerCommand(interface=self.server, _callable=doc_test)
        value = command.__doc__()
        assert value == 'FooBar'

    # ------------------------------------------------------------------------------------------------------------------
    def test_verbose_help(self):
        def doc_test():
            """FooBar"""
            return True

        command = clacks.ServerCommand(interface=self.server, _callable=doc_test)
        command.help(verbose=True)

    # ------------------------------------------------------------------------------------------------------------------
    def test_create_bad_command(self):
        try:
            command = clacks.ServerCommand(interface=self.server, _callable=None)
            self.fail()
        except ValueError:
            pass

        def foo():
            print('bar')

        try:
            command = clacks.ServerCommand(interface=None, _callable=foo)
            self.fail()
        except ValueError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_command_key(self):
        try:
            self.server.register_command('bad command key', foo)
            self.fail()
        # -- this should raise a ValueError
        except KeyError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_command_value(self):
        try:
            self.server.register_command('key', None)
            self.fail()
        # -- this should raise a ValueError
        except ValueError:
            pass
