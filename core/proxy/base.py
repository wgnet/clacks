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

ClientProxyBase
===============

Client proxies are simple objects that operate as a thin API wrapper between the user and the server they are trying
to communicate with, making them ideal as interfaces and intellisense containers for more well-known servers.

An enduring problem with proxies and the servers they interact with, is that at code time, code hinting is not supported
for remote objects, as they do not exist yet. The proxy class, while also providing basic methods for sending and
receiving data, is built as a way to solve this problem, since a user can choose to provide as many methods as they
want.

This makes it possible, using modules like inspect, to automatically generate a Proxy Class with its methods
implemented, without needing to make the code that generates these classes too complex.

"""
import functools
import logging
import socket
import threading
import time
import typing
import uuid

from .utils import register_proxy_type
from ..command import ServerCommand
from ..adapters import ServerAdapterBase
from ..handler import BaseRequestHandler
from ..interface import ServerInterface, proxy_interface_from_type
from ..package import Question, Response


# ----------------------------------------------------------------------------------------------------------------------
class ClientProxyBase(object):

    connection_retries = 5

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, address, handler, connect=True):
        if not isinstance(address, tuple):
            raise TypeError('Address must be a tuple, got %s!' % type(address))

        if not isinstance(address[0], (str, bytes)):
            raise TypeError('Host must be a string, got %s' % type(address[0]))

        if not isinstance(address[1], int):
            raise TypeError('Port must be an integer, got %s' % type(address[1]))

        if not isinstance(handler, BaseRequestHandler):
            raise TypeError('Handler must be a BaseRequestHandler, got %s' % type(handler))

        self.logger = logging.getLogger('Client Proxy')

        self.debug = False

        self.logger.debug('Setting up socket @ %s' % str(address))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.logger.debug('Registering handler type %s' % handler)
        self.handler = handler

        self.address = address

        self.proxy_commands = dict()
        self.server_commands = list()

        self.interfaces = dict()
        self.adapters = list()

        if connect:
            self.connect()

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        return '[%s] @ %s' % (self.__class__.__name__, str(self.address))

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def connected(self) -> bool:
        try:
            self.socket.getsockname()
            return True
        except socket.error:
            return False

    # ------------------------------------------------------------------------------------------------------------------
    def register_interface_by_type(self, interface_type: str) -> bool:
        """
        From a key string, register an interface that indicates the type of the interface.

        :param interface_type: the interface type to create and register
        :type interface_type: str

        :return: True if registry was successful
        """
        interface = proxy_interface_from_type(interface_type)
        if interface is None:
            raise ValueError('Interface Type %s could not be found in the interface registry!' % interface_type)

        if interface_type in self.interfaces:
            self.logger.warning('Server %s already implements interface %s!' % (self, interface_type))
            return False

        interface = interface()
        self.register_interface(interface_type, interface)
        return True

    # ------------------------------------------------------------------------------------------------------------------
    def register_interface(self, key, interface):
        # type: (str, ServerInterface) -> None
        """
        Register an interface object instance, exposing its methods on this server.

        :param key: Interface key to register under
        :type key: str

        :param interface: ServerInterface instance to register
        :type interface: ServerInterface

        :return: None
        """
        if not isinstance(interface, ServerInterface):
            raise TypeError('Expected ServerInterface, got %s!' % type(interface))
        self.interfaces[key] = interface
        interface.register(self)

    # ------------------------------------------------------------------------------------------------------------------
    def register_command(self, key: str, command: ServerCommand):
        if not isinstance(command, ServerCommand):
            raise TypeError('_callable parameter must be callable! got: %s' % type(command))
        self.proxy_commands[key] = command

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter(self, adapter):
        # type: (ServerAdapterBase) -> None
        if not isinstance(adapter, ServerAdapterBase):
            raise TypeError('%s is not a ServerAdapterBase instance!' % adapter)
        self.adapters.append(adapter)
        self.handler.register_adapter(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def disconnect(self):
        if not self.connected:
            return True
        result = self.question('disconnect_client', self.socket.getsockname()).response
        self.socket.close()
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__.get(key)

        if self.__dict__['proxy_commands'].get(key):
            return self.proxy_commands.get(key)

        return functools.partial(self.question, key)

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self):
        self.handler.register_server(self)
        self.handler._initialize(self)

    # ------------------------------------------------------------------------------------------------------------------
    def connect(self):
        """
        Connect this proxy to the given address.

        :return: None
        """
        self._initialize()

        retries = 1
        while not self.connected and retries <= self.connection_retries:
            try:
                self.socket.connect(self.address)
            except socket.error:
                self.logger.warning('Failed %s connection attempts to %s. Retrying.' % (retries, str(self.address)))
            retries += 1

        if not self.connected:
            raise socket.error('Could not connect to address %s!' % str(self.address))

        self.logger.debug('Successfully connected to socket %s' % str(self.address))

        self.logger.debug('Fetching server commands...')

        # type: Response
        response = self.timed_question('list_commands', timeout=10.0)

        self.logger.warning('Took %s seconds for initial request.' % response.payload['response_time'])

        if response is not None and response.traceback:
            traceback_type = Exception
            if response.traceback_type is not None:
                traceback_type = response.traceback_type
            raise traceback_type(response.traceback)

        server_commands = response.response

        if not isinstance(server_commands, (tuple, list)):
            raise ValueError('Could not fetch server commands from server!')

        self.server_commands = sorted(list(set(server_commands)))

        self.logger.debug('Server commands successfully fetched!')

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, data, timeout=None):
        # type: (Question, float) -> typing.Tuple[dict, Response]
        if timeout is None:
            self.handler.send(self.socket, transaction_id=str(uuid.uuid4()), package=data)
            return self.handler.receive_response(self.socket)

        else:
            # -- this works with a list to track whether anything has been received
            response = []

            start = time.time()

            def _send():
                self.handler.send(self.socket, transaction_id=str(uuid.uuid4()), package=data)
                response.append(self.handler.receive_response(self.socket))

            thread = threading.Thread(target=_send)
            thread.daemon = True
            thread.start()

            while (time.time() - start) < timeout:
                if response:
                    break
                time.sleep(0.1)

            if not response:
                raise ValueError('Question did not return with a response within {} seconds!'.format(timeout))

            response = response[0]
            header, response = response[0], response[1]

            # -- log the response time
            response.payload['response_time'] = time.time() - start

            return header, response

    # ------------------------------------------------------------------------------------------------------------------
    def command_exists(self, command):
        # type: (Response) -> bool
        return command in self.server_commands

    # ------------------------------------------------------------------------------------------------------------------
    def question(self, command, *args, **kwargs):
        # type: (str, typing.Union[list, None], typing.Union[dict, None]) -> typing.Union[Response, None]
        timeout = None
        if 'timeout' in kwargs:
            timeout = kwargs.get('timeout', None)
            del kwargs['timeout']

        question = Question(
            dict(Connection='keep-alive'),
            command,
            *args,
            **kwargs
        )

        header_data, response = self.send(question, timeout=timeout)

        if response is not None and response.traceback:
            raise response.traceback_type(response.traceback)

        return response

    # ------------------------------------------------------------------------------------------------------------------
    def timed_question(self, command, timeout=5.0, *args, **kwargs):
        # type: (str, float, typing.Union[list, None], typing.Union[dict, None]) -> typing.Union[Response, None]
        question = Question(
            dict(Connection='keep-alive'),
            command,
            *args,
            **kwargs
        )

        header_data, response = self.send(question, timeout=timeout)

        if response is not None and response.traceback:
            traceback_type = Exception
            if response.traceback_type is not None:
                traceback_type = response.traceback_type
            raise traceback_type(response.traceback)

        return response


register_proxy_type('default', ClientProxyBase)
