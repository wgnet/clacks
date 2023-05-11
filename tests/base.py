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
import logging
import unittest


_server = None
_address = None
_client = None


# ----------------------------------------------------------------------------------------------------------------------
class TestServerInterface(clacks.ServerInterface):

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.takes({'first': int, 'second': str})
    def takes(self, first, second):
        return first, second

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.returns(str)
    def returns(self):
        return 'string'

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.returns_status_code
    def returns_status_code(self):
        return True, 666

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.returns_status_code
    def returns_status_code_bad(self):
        return True

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.aka(['PRINCE'])
    def aka(self, arg):
        return arg

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.private
    def private_fn(self, value):
        print('This should not be reachable')

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.fka(['prince'])
    def artist(self):
        return True

    # ------------------------------------------------------------------------------------------------------------------
    @clacks.decorators.returns(clacks.Response)
    def returns_response(self):
        return clacks.Response(
            header_data=dict(),
            response='foo bar',
            code=667,
        )


clacks.register_server_interface_type('decorator_test', TestServerInterface)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksTestCase(unittest.TestCase):

    handler_type = clacks.SimpleRequestHandler
    marshaller_type = clacks.SimplePackageMarshaller

    server_interfaces = [
        'standard',
        'cmd_utils',
        'profiling',
        'logging',
        'file_io',
        'decorator_test',
    ]

    proxy_interfaces = [
        'standard',
        'logging',
        'file_io',
    ]

    rebuild_server = False

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, methodName):
        super(ClacksTestCase, self).__init__(methodName)

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

        # -- initialize everything
        _ = self.server
        _ = self.client

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):
        global _server
        global _address
        global _client

        if cls.rebuild_server:
            if _server is not None:
                _client.disconnect()
                _server.end()

            _server = None
            _address = None
            _client = None

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        global _server
        global _address
        global _client

        if cls.rebuild_server:
            if _server is not None:
                _client.disconnect()
                _server.end()

            _server = None
            _address = None
            _client = None

        _server, _address = cls.build_server()
        _client = cls.build_client()

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def build_client(cls):
        c = clacks.ClientProxyBase(_address, clacks.SimpleRequestHandler(clacks.SimplePackageMarshaller()))

        for interface in cls.proxy_interfaces:
            c.register_interface_by_type(interface)

        return c

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def build_server(cls):
        s = clacks.ServerBase('Unittest Server')

        for interface in cls.server_interfaces:
            s.register_interface_by_key(interface)

        a = s.register_handler_by_key('localhost', 0, 'simple', 'simple')

        # -- we want our server to throw deprecation warnings
        s.register_adapter_by_key('deprecation_warnings')

        s.start(blocking=False)

        return s, a

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def server(self):
        global _server
        global _address

        if _server is not None:
            return _server

        _server, _address = self.build_server()
        return _server

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def client(self):
        global _client

        if _client is not None:
            return _client

        _client = self.build_client()

        return _client

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def get_server_instance(cls):
        server = clacks.ServerBase(identifier='Test Server')

        for interface in cls.server_interfaces:
            server.register_interface_by_key(interface)

        handler = cls.handler_type(cls.marshaller_type())
        host, port = 'localhost', clacks.get_new_port('localhost')

        server.register_handler(host, port, handler)
        return server, (host, port)

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def get_client_instance(cls, address):
        client = clacks.ClientProxyBase(
            address,
            handler=cls.handler_type(cls.marshaller_type())
        )

        for interface in cls.proxy_interfaces:
            client.register_interface_by_type(interface)

        client.register_interface_by_type('standard')
        return client

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def create_handler(cls):
        handler = cls.handler_type(cls.marshaller_type())
        handler._initialize(cls)
        return handler

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def example_header_data(cls, keep_alive=True):
        result = {
            'Content-Length': 1546,
            'Accept-Encoding': 'text/json',
        }

        if keep_alive:
            result['Connection'] = 'keep-alive'

        return result
