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

    _ADDRESS = _CLIENT = _SERVER = None

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, methodName):
        super(ClacksTestCase, self).__init__(methodName)

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

    # ------------------------------------------------------------------------------------------------------------------
    def build_client(self):
        c = self.build_client_instance()

        for interface in self.proxy_interfaces:
            c.register_interface_by_type(interface)

        return c

    # ------------------------------------------------------------------------------------------------------------------
    def build_client_instance(self):
        return clacks.ClientProxyBase(self.address, self.create_handler())

    # ------------------------------------------------------------------------------------------------------------------
    def build_server_instance(self):
        return clacks.ServerBase('Unittest Server')

    # ------------------------------------------------------------------------------------------------------------------
    def build_server(self):
        s = self.build_server_instance()

        for interface in self.server_interfaces:
            s.register_interface_by_key(interface)

        a = s.register_handler('localhost', 0, self.create_handler())

        # -- we want our server to throw deprecation warnings
        s.register_adapter_by_key('deprecation_warnings')

        s.start(blocking=False)

        return s, a

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def address(self):
        if self._SERVER is not None:
            return self._ADDRESS
        self._SERVER, self._ADDRESS = self.build_server()
        return self._ADDRESS

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def server(self):
        if self._SERVER is not None:
            return self._SERVER
        self._SERVER, self._ADDRESS = self.build_server()
        return self._SERVER

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def client(self):
        if self._CLIENT is not None:
            return self._CLIENT

        self._CLIENT = self.build_client()
        return self._CLIENT

    # ------------------------------------------------------------------------------------------------------------------
    def get_server_instance(self):
        server = clacks.ServerBase(identifier='Test Server')

        for interface in self.server_interfaces:
            server.register_interface_by_key(interface)

        handler = self.create_handler()
        host, port = 'localhost', clacks.get_new_port('localhost')

        server.register_handler(host, port, handler)
        return server, (host, port)

    # ------------------------------------------------------------------------------------------------------------------
    def get_client_instance(self, address):
        client = clacks.ClientProxyBase(
            address,
            handler=self.create_handler()
        )

        for interface in self.proxy_interfaces:
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
