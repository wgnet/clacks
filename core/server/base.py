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
import gc
import time
import uuid
import socket
import typing
import logging
import threading
import traceback

from ..constants import LOG_MSG_LENGTH
from ..errors.codes import ReturnCodes
from ..package import Question, Response
from ..marshaller import marshaller_from_key
from ..interface.base import ServerInterface
from ..utils import get_new_port, is_key_legal
from ..adapters import ServerAdapterBase, adapter_from_key
from ..handler import BaseRequestHandler, handler_from_key
from ..interface.constants import server_interface_from_type
from ..errors import ClacksClientConnectionFailedError, error_code_from_error
from ..command import ServerCommand, ServerCommandDigestLoggingHandler, command_from_callable


# ----------------------------------------------------------------------------------------------------------------------
class ServerBase(object):
    """
    Base Server class; this class is at the base of every Clacks implementation, and is the beating heart of
    Clacks.
    """

    _REQUIRED_INTERFACES: list[str] = []

    _REQUIRED_ADAPTERS: list[str] = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, identifier=None, start_queue=True, threaded_digest=False):
        # type: (typing.Union[str, None], bool, bool) -> None
        """
        Create a new server.

        :param identifier: the name of the server.
        :type identifier: str

        :param start_queue: if True, start the digest queue immediately instead of when "start()" is called.
        :type start_queue: bool

        :param threaded_digest: if True, the server's digest is threaded; mostly used for dispatch servers.
        :type threaded_digest: bool
        """
        self.startup_start_time = time.time()

        self.identifier = str(identifier) if identifier is not None else str(uuid.uuid4())

        self.sockets = dict()
        self.handler_addresses = dict()

        self.logger = logging.getLogger(self.identifier)

        self.threaded_digest = threaded_digest

        self.clients = list()

        # -- store a list of connections by client
        self.connections = dict()

        self.commands = dict()

        self.queue = list()
        self.queue_started = False

        self.busy = False
        self.stopped = False

        self.worker_thread = None
        self.handler_threads = dict()
        self.queue_threads = list()

        self.interfaces = dict()
        self.adapters = dict()

        self.command_handler = ServerCommandDigestLoggingHandler()

        # -- register required interfaces on init
        for key in self._REQUIRED_INTERFACES:
            self.register_interface_by_key(key)

        for key in self._REQUIRED_ADAPTERS:
            self.register_adapter_by_key(key)

        if start_queue:
            self.start_queue()

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter_by_key(self, adapter_key):
        adapter = adapter_from_key(adapter_key)
        self.register_adapter(adapter_key, adapter())

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter(self, key, adapter, handler_types=None):
        if not isinstance(adapter, ServerAdapterBase):
            raise TypeError('Expected a ServerAdapterBase instance, got %s!' % adapter)

        # -- the following two blocks will lead to a recursive loop, though not an infinite one, as interfaces that
        # -- have already been registered will not be registered twice, and so interfaces can be dependent on each
        # -- other without causing a loop.
        for value in adapter.REQUIRED_INTERFACES:
            if value in self.interfaces:
                continue
            self.register_interface_by_key(value)

        for value in adapter.REQUIRED_ADAPTERS:
            if value in self.adapters:
                continue
            self.register_adapter_by_key(value)

        self.adapters[key] = adapter

        for client in self.handler_threads:
            if handler_types is None:
                client.register_adapter(adapter)
            else:
                for typ in handler_types:
                    if not isinstance(client.handler, typ):
                        continue
                    client.register_adapter(adapter)

        for handler in self.handler_addresses:
            if handler_types is None:
                handler.register_adapter(adapter)

            else:
                for typ in handler_types:
                    if not isinstance(handler, typ):
                        continue
                    handler.register_adapter(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]

        if self.get_command(item):
            return self.get_command(item)

        for interface in self.interfaces.values():
            if hasattr(interface, item):
                return getattr(interface, item)

        raise AttributeError

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return '[%s] %s' % (self.__class__.__name__, self.identifier)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def handlers(self):
        return list(self.handler_addresses.keys())

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def socket_addresses(self):
        """
        Return a list of addresses this server's handlers are listening to.

        :return: list of (host, port) tuples
        :rtype: list
        """
        result = list()
        for sock in self.sockets:
            try:
                # -- the socket may be disconnected at this time, but if it is, the server will take care of it.
                result.append(sock.getsockname())
            except Exception:
                pass
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def load_spec(self, spec):
        # type: (dict) -> None
        """
        Load a spec from a given dictionary, allowing a server to set itself up completely from something as simple as,
        say, a JSON file. This allows a developer to store a prefab server construction offline, rather than having to
        hard-code it in template functions.

        :param spec: dictionary containing the spec of the server to set up.
        :type spec: dict

        :return: None
        :rtype: NoneType
        """
        if not isinstance(spec, dict):
            raise TypeError('Server specs have to be provided as a dictionary!')

        for interface in spec.get('interfaces', list()):
            self.register_interface_by_key(interface_type=interface)

        for adapter in spec.get('adapters', list()):
            self.register_adapter_by_key(adapter)

        for handler in spec.get('handlers', list()):
            handler_key = handler.get('key')
            marshaller_key = handler.get('marshaller')
            host = handler.get('host')
            port = handler.get('port')
            self.register_handler_by_key(host, port, handler_key, marshaller_key)

    # ------------------------------------------------------------------------------------------------------------------
    def register_interface(self, key, interface):
        # type: (str, ServerInterface) -> None
        """
        Register an interface object instance, exposing its methods on this server.

        :param key: interface key to register
        :type key: str

        :param interface: ServerInterface instance to register
        :type interface: ServerInterface

        :return: None
        """
        if not isinstance(interface, ServerInterface):
            raise TypeError('Expected ServerInterface, got %s!' % type(interface))

        self.interfaces[key] = interface

        # -- the following two blocks will lead to a recursive loop, though not an infinite one, as interfaces that
        # -- have already been registered will not be registered twice, and so interfaces can be dependent on each
        # -- other without causing a loop.
        for value in interface._REQUIRED_INTERFACES:
            if value in self.interfaces:
                continue
            self.register_interface_by_key(value)

        for value in interface._REQUIRED_ADAPTERS:
            if value in self.adapters:
                continue
            self.register_adapter_by_key(value)

        interface.register(self)

    # ------------------------------------------------------------------------------------------------------------------
    def register_interface_by_key(self, interface_type):
        # type: (str) -> None
        """
        From a key string, register an interface that indicates the type of the interface.

        :param interface_type: the interface type to create and register
        :type interface_type: str

        :return: None
        """
        interface = server_interface_from_type(interface_type)

        if interface is None:
            raise ValueError('Interface Type %s could not be found in the interface registry!' % interface_type)

        if interface_type in self.interfaces:
            self.logger.warning('Server %s already implements interface %s!' % (self, interface_type))
            return

        interface = interface()
        self.register_interface(interface_type, interface)

    # ------------------------------------------------------------------------------------------------------------------
    def register_handler_by_key(self, host, port, handler_key, marshaller_key):
        # type: (str, int, str, str) -> typing.Tuple[str, int]
        """
        On the given host, automatically acquire a new port and register the given handler type to it, using the given
        marshaller type.

        This function internalizes the mechanism of acquiring a new port, making it easier to write shorthand.

        This makes it possible to call this function with much simpler syntax:

        # -- open a port on localhost, using a JSONHandler with a JSONMarshaller
        host, port = server.register_handler('localhost', 'json', 'json')

        :param host: name of the host on which to register the port
        :type host: str

        :param port: if wanted, a user can pass a port number they want to register the handler on.
        :type port: int

        :param handler_key: handler type (registry key)
        :type handler_key: str

        :param marshaller_key: marshaller type (registry key)
        :type marshaller_key: str

        :return: tuple of (host, port)
        :rtype: Tuple(str, int)
        """
        if port == 0:
            port = get_new_port(host)

        handler_type = handler_from_key(handler_key)
        marshaller_type = marshaller_from_key(marshaller_key)

        self.register_handler(host, port, handler_type(marshaller_type()))

        return host, port

    # ------------------------------------------------------------------------------------------------------------------
    def register_handler(self, host, port, handler):
        # type: (str, int, BaseRequestHandler) -> None
        """
        Register the provided handler on this server and make it listen on the (host, port) address.

        :param host: the host to register the handler on
        :type host: str

        :param port: the port to register the handler on
        :type port: int

        :param handler: The handler we should make listen on the port.
        :type handler: BaseRequestHandler

        :return: None
        """
        if not isinstance(host, (str, bytes)):
            raise TypeError('Expected string value for host argument, got %s!' % type(host))

        if not isinstance(port, int):
            raise TypeError('Expected integer value for port argument, got %s!' % type(port))

        if not isinstance(handler, BaseRequestHandler):
            raise TypeError('Expected BaseRequestHandler instance for handler argument, got %s!' % type(handler))

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.setblocking(True)
        sock.bind((str(host), int(port)))

        self.sockets[sock] = handler
        self.handler_addresses[handler] = host, port
        handler.register_server(self)

        for adapter in self.adapters.values():
            handler.register_adapter(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def tick_queue(self):
        # type: () -> None
        if not len(self.queue):
            time.sleep(0.001)
            return

        if self.busy:
            time.sleep(0.001)
            return

        self.busy = True

        # -- pop the queue first
        _args = self.queue.pop(0)

        for adapter in self.adapters.values():
            adapter.server_post_remove_from_queue(self, *_args)

        if self.threaded_digest:
            thread = threading.Thread(target=self.__respond, args=_args)
            thread.daemon = True
            thread.start()

            # -- keep it from being garbage collected immediately
            self.queue_threads.append(thread)

        else:
            self.__respond(*_args)

        self.busy = False

    # ------------------------------------------------------------------------------------------------------------------
    def start_queue(self, *args):
        # type: (list) -> None
        self.logger.debug('Starting Queue')

        def _start_queue():
            while not self.stopped:
                self.tick_queue()

        self.worker_thread = threading.Thread(target=_start_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()

        self.queue_started = True

        root_logger = logging.getLogger()
        root_logger.addHandler(self.command_handler)

    # ------------------------------------------------------------------------------------------------------------------
    def __respond(self, handler, connection, transaction_id, header_data, data):
        try:
            self._respond(handler, connection, transaction_id, header_data, data)

        except Exception as e:
            tb = traceback.format_exc()

            response = Response(
                header_data={'Content-Type': header_data.get('Content-Type', 'text/json')},
                response=None,
                code=error_code_from_error(e),
                tb=tb,
                tb_type=type(e),
            )

            # -- the handler must respond, no matter what.
            handler.respond(connection, transaction_id, response)

    # ------------------------------------------------------------------------------------------------------------------
    def _respond(self, handler, connection, transaction_id, header_data, data):
        # type: (BaseRequestHandler, socket.socket, str, dict, dict) -> None
        """
        From a given set of transaction data, respond to the provided request using the given handler and connection.
        This ensures that a request made on a connection is always responded to on that same connection, in the order
        it came into that connection, no matter how many clients are connected to the server at the same time.

        :param handler: the handler that received the transaction and that will respond to it.
        :type handler: BaseRequestHandler

        :param connection: socket object that will receive the response to this transaction.
        :type connection: socket.socket

        :param transaction_id: this transaction's ID, useful for lookup-based mechanisms.
        :type transaction_id: str

        :param header_data: the header data for the transaction
        :type header_data: dict

        :param data: the data in the transaction
        :type data: dict

        :return: None
        """
        for adapter in self.adapters.values():
            adapter.server_pre_digest(self, handler, connection, transaction_id, header_data, data)

        self.command_handler.start()

        try:
            response = self.digest(handler, connection, transaction_id, header_data, data)

        except Exception as e:
            tb = traceback.format_exc()

            response = Response(
                header_data={'Content-Type': header_data.get('Content-Type', 'text/json')},
                response=None,
                code=error_code_from_error(e),
                tb=tb,
                tb_type=type(e),
            )

        # -- inject warnings and errors
        response.errors += self.command_handler.errors
        response.warnings += self.command_handler.warnings

        self.command_handler.stop()

        for adapter in self.adapters.values():
            adapter.server_post_digest(self, handler, connection, transaction_id, header_data, data, response)

        handler.respond(connection, transaction_id, response)

    # ------------------------------------------------------------------------------------------------------------------
    def digest(self, handler, connection, transaction_id, header_data, data):
        # type: (BaseRequestHandler, socket.socket, str, dict, dict) -> Response
        """
        Digest a package, using header data and data. This creates a Response instance.

        :param handler: the handler this transaction came in through
        :type handler: BaseRequestHandler

        :param connection: socket object that will receive the response to this transaction.
        :type connection: socket.socket

        :param transaction_id: this transaction's ID, useful for lookup-based mechanisms.
        :type transaction_id: str

        :param header_data: header data
        :type header_data: dict

        :param data: package data
        :type data: dict

        :return: digest result
        :rtype: Response
        """
        try:
            question = Question.load(header_data, data)

        except Exception as e:
            exc_info = traceback.format_exc()

            response = Response(
                header_data=header_data,
                response=None,
                code=ReturnCodes.BAD_QUESTION,
                tb=exc_info,
                info=dict(),
                tb_type=type(e),
            )

            self.logger.exception('Handler %s Failed loading question from header %s with data %s' % (
                handler,
                str(header_data),
                str(data))
                                  )

            self.logger.exception(exc_info)

            response.accept_encoding = header_data.get('Accept-Encoding', 'text/json')
            return response

        cmd = self.get_command(question.command)

        if cmd is None:
            self.logger.exception('Given command %s is not registered!' % question.command)
            response = Response(
                header_data=header_data,
                response=None,
                code=ReturnCodes.NOT_FOUND,
                tb='Given command %s is not registered!' % question.command,
                info=dict()
            )
            response.accept_encoding = header_data.get('Accept-Encoding', 'text/json')
            return response

        question.accept_encoding = header_data.get('Accept-Encoding', 'text/json')

        self.logger.debug('Digesting {question}...'.format(question=str(question)[:LOG_MSG_LENGTH]))

        response = self._digest(cmd, question)

        return response

    # ------------------------------------------------------------------------------------------------------------------
    def _digest(self, command, question):
        # type: (ServerCommand, Question) -> Response
        """

        :param command:
        :type command: ServerCommand

        :param question:
        :type question: Question

        :return:
        :rtype: Response
        """
        # -- this is wrapped at the highest level because we do not want this to fail in any case.
        # -- we also specifically disable the broad exception catch for this

        # noinspection PyBroadException
        try:
            response = command.digest(question)
            return response

        except Exception as e:
            tb = traceback.format_exc()

            return Response(
                header_data={'Content-Type': question.header_data.get('Content-Type', 'text/json')},
                response=None,
                code=error_code_from_error(e),
                tb=tb,
                tb_type=type(e),
            )

    # ------------------------------------------------------------------------------------------------------------------
    def add_to_queue(self, handler, connection, transaction_id, header_data, data):
        # type: (BaseRequestHandler, socket.socket, str, dict, dict) -> None
        """
        Add a transaction to the queue.

        :param handler: request handler on which the transaction arrived.
        :type handler: BaseRequestHandler

        :param connection: connection object
        :type connection: socket.socket

        :param transaction_id: transaction ID for the transaction, unique identifier
        :type transaction_id: str

        :param header_data: header data
        :type header_data: dict

        :param data: package data
        :type data: dict

        :return: None
        """
        for adapter in self.adapters.values():
            if adapter not in handler.adapters:
                continue
            adapter.server_pre_add_to_queue(self, handler, connection, transaction_id, header_data, data)

        self.queue.append((handler, connection, transaction_id, header_data, data))
        self.logger.debug('Item %s added to queue. Queue contains %s items.' % (str(data), len(self.queue)))

    # ------------------------------------------------------------------------------------------------------------------
    def register_command(self, key, _callable, skip_duplicates=False):
        # type: (str, (callable, ServerCommand), bool) -> None
        """
        Register a callable object as a ServerCommand instance. This will work with the data created by the
        server_command decorator.

        :param key: alias under which to register the command
        :type key: str

        :param _callable: callable method
        :type _callable: callable

        :param skip_duplicates: if True, skip registering methods on previously occupied keys.
        :type skip_duplicates: bool

        :return: None
        """
        # -- we cannot register a command that isn't callable
        if not callable(_callable):
            raise ValueError('_callable parameter must be callable! Given: %s' % type(_callable))

        # -- by default, we automatically turn a function into a ServerCommand when we don't get one fed to us.
        if not isinstance(_callable, ServerCommand):
            command = command_from_callable(interface=self, function=_callable, cls=ServerCommand)
            if command is None:
                self.logger.debug('Could not create a ServerCommand from function %s - ignoring.' % _callable.__name__)
                return
            _callable = command

        # -- a command must always be known as itself
        if key not in _callable.aliases:
            _callable.aliases.append(key)

        self._register_command(key, _callable)

    # ------------------------------------------------------------------------------------------------------------------
    def _register_command(self, key, srv_cmd):
        # type: (str, ServerCommand) -> None
        """
        Private method to register a command, only accepts pure ServerCommand instances and is expected to be called
        internally only. To register a command, use "register_command" instead. This is necessary for all aliases
        and type hints to be discovered.

        :param key: alias under which to register the command
        :type key: str

        :param srv_cmd: ServerCommand instance
        :type srv_cmd: ServerCommand

        :return: None
        """
        # -- do not register commands that are illegal
        if not is_key_legal(key):
            raise KeyError('Key "%s" is not legal for a command!' % key)

        # -- in this method, we cannot register commands that are not a ServerCommand instance.
        if not isinstance(srv_cmd, ServerCommand):
            raise ValueError('_register_command requires a ServerCommand instance!')

        # -- if the key collides with one already in the registry, notify the developer but this is not a failure case
        # -- as some interfaces might override others' commands intentionally. This is a messy way to work though,
        # -- so throw a warning regardless.
        if self.commands.get(key) is not None:
            msg = 'Command key %s is being assigned twice - is not allowed!' % key
            self.logger.error(msg)
            raise Exception(msg)

        # -- register the command
        self.commands[key] = srv_cmd

        self.logger.info('Registered Command [%s]: %s' % (key, srv_cmd))

    # ------------------------------------------------------------------------------------------------------------------
    def remove_client(self, client):
        # type: (ServerClient) -> bool
        """
        Remove the given client instance from the list of clients.

        :param client: ServerClient instance to remove
        :type client: ServerClient

        :return: True if the client was removed successfully
        :rtype: bool
        """
        if client not in self.clients:
            raise ValueError('Attempted to disconnect unregistered client: {client}'.format(client=client))

        self.logger.warning('Removing client %s from list' % client)
        self.clients.pop(self.clients.index(client))

        # -- attempt to clean up
        if client.connection in self.connections:
            del self.connections[client.connection]

        if client in self.handler_threads:
            del self.handler_threads[client]

        return True

    # ------------------------------------------------------------------------------------------------------------------
    def add_client(self, connection, address, handler):
        # type: (socket.socket, tuple, BaseRequestHandler) -> None
        """
        Add a new client from a given connection, and keep it open and stored. This allows us to connect multiple
        simultaneous clients. This method starts a thread.

        :param connection: socket object.
        :type connection: socket.socket

        :param address: (host, port)
        :type address: tuple

        :param handler: BaseRequestHandler instance
        :type handler: BaseRequestHandler

        :return: None
        """
        if (address[0], address[1]) in self.socket_addresses:
            raise ValueError('Attempted to connect to self!')

        client = ServerClient(
            self,
            connection=connection,
            address=address,
            handler=handler,
            on_connection_closed=self.remove_client
        )

        client._initialize(self)

        self.connections[connection] = client

        self.logger.info('Adding client "%s"' % client)
        self.clients.append(client)

        thread = threading.Thread(target=client.start)
        thread.daemon = True
        thread.start()

        self.handler_threads[client] = thread

    # ------------------------------------------------------------------------------------------------------------------
    def _disconnect_client(self, address):
        # type: (tuple) -> bool
        """
        Disconnect the given client from this server.

        :param address: tuple of (host, socket) to disconnect.
        :type address: tuple

        :return: True if successful
        :rtype: bool
        """
        if not isinstance(address, (list, tuple)):
            raise ValueError('Expected a list or tuple with 2 indices, got %s!' % type(address))

        if len(address) != 2:
            raise ValueError('Expected a list or tuple with 2 indices, got %s indices!' % len(address))

        host, port = address

        # -- type sanitation - port may be passed as a string
        address = (str(host), int(port))

        for client in self.clients:
            if client.address != address:
                continue
            self.remove_client(client)
            return True

        return False

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self):
        # type: () -> bool
        """
        This method is called just before the server is started - this gives handlers, adapters and interfaces the
        opportunity to do some last-minute changes and resource gathering.

        :return: True if successful, if False, the server will not be started.
        :rtype: bool
        """
        success = True

        for handler in self.handler_addresses:
            _success = handler._initialize(self)
            success = success or _success

        for adapter in self.adapters.values():
            _success = adapter._initialize(self)
            success = success or _success

        for interface in self.interfaces.values():
            _success = interface._initialize(self)
            success = success or _success

        return success

    # ------------------------------------------------------------------------------------------------------------------
    def start(self, blocking=False):
        # type: (bool) -> None
        """
        Start the server, accepting a maximum queue length of pending connections of 5. This method loops forever,
        and will block if not threaded.

        :param blocking: if True, will return this method once the server has started and not block the thread.
        :type blocking: bool

        :return: None
        """
        can_boot = self._initialize()

        if not can_boot:
            raise Exception('Server initialize() method returned False - server boot sequence aborted!')

        for sock, handler in self.sockets.items():
            self.start_socket(sock, handler)

        if not self.queue_started:
            self.start_queue()

        self.logger.warning('Took %s seconds to start up server.' % (time.time() - self.startup_start_time))

        if blocking:
            while not self.stopped:
                time.sleep(1.0)

    # ------------------------------------------------------------------------------------------------------------------
    def start_socket(self, sock, handler):
        # type: (socket.socket, BaseRequestHandler) -> None
        """
        For a given connection, start a handler reception queue. This is called for every handler.

        :param sock: socket instance to make the handler instance listen to.
        :type sock: socket.socket

        :param handler: BaseRequestHandler instance
        :type handler: BaseRequestHandler

        :return: None
        """

        def _start():
            sock.listen(5)

            self.logger.warning(
                'Server "%s" started. Public Interface available @ %s - Handler: %s' % (
                    self.identifier,
                    sock.getsockname(),
                    handler,
                )
            )

            while not self.stopped:
                # -- handlers decide how to accept the connection.
                try:
                    connection, address = handler.accept_socket(sock=sock)
                    self.add_client(connection=connection, address=address, handler=handler)
                except ClacksClientConnectionFailedError:
                    if not self.stopped:
                        self.logger.warning('Client connection failed!')
                time.sleep(0.5)

        thread = threading.Thread(target=_start)
        thread.daemon = True
        thread.start()

        self.handler_threads[handler] = thread

    # ------------------------------------------------------------------------------------------------------------------
    def end(self):
        # type: () -> None
        """
        Shut down the server. This closes all sockets.

        :return: None
        """
        if self.stopped:
            raise Exception('Server %s already stopped!' % self)

        self.logger.warning('shutting down server %s' % self)

        self.stopped = True
        self.queue_started = False

        for client in self.clients:
            self.remove_client(client)

        for sock in self.sockets:
            sock.close()

        if hasattr(self, 'worker_thread') and self.worker_thread is not None:
            del self.worker_thread

        self.handler_addresses = dict()
        self.handler_threads = dict()

        gc.collect()

    # ------------------------------------------------------------------------------------------------------------------
    def get_command(self, key):
        # type: (str) -> ServerCommand
        """
        Get a ServerCommand instance by its lookup key. This is the same as the command alias.

        :param key: the key to use to look up the command in question
        :type key: str

        :return: ServerCommand instance registered under this key
        :rtype: ServerCommand
        """
        return self.commands.get(key)


# ----------------------------------------------------------------------------------------------------------------------
class ServerClient(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, server, connection, address, handler, on_connection_closed=None):
        # type: (ServerBase, socket.socket, tuple, BaseRequestHandler, callable) -> None
        self.parent = None
        self.server = server
        self.connection = connection
        self.address = address
        self.handler = handler

        self.on_connection_closed = on_connection_closed

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self, parent):
        self.parent = parent
        self.handler._initialize(self)

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter_by_key(self, adapter_key):
        adapter = adapter_from_key(adapter_key)
        self.register_adapter(adapter())

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter(self, adapter):
        if not isinstance(adapter, ServerAdapterBase):
            raise TypeError('%s is not a ServerAdapterBase instance!' % adapter)
        self.handler.register_adapter(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return '%s-[Client]->%s' % (self.server, self.address)

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        # type: () -> None

        # -- cache the connection handle, so we can print it later without needing to request it, which would crash.
        connection_handle = self.connection.getsockname()

        try:
            self.server.logger.warning('Beginning revc_forever on %s' % str(connection_handle))
            self.handler.recv_forever(self.connection)

        except socket.error:
            self.server.logger.exception('Disconnected %s' % str(connection_handle))
            pass

        if self.on_connection_closed is not None:
            self.on_connection_closed(self)
