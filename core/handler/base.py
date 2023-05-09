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
import collections
import logging
import socket
import sys
import time
import traceback
import typing
import uuid

from .constants import HandlerErrors
from ..constants import LOG_MSG_LENGTH
from ..errors import ClacksClientConnectionFailedError
from ..errors.codes import ReturnCodes
from ..marshaller import BasePackageMarshaller
from ..package import Package, Question, Response

_unicode = bytes
if sys.version_info.major == 2:
    _unicode = unicode


# ----------------------------------------------------------------------------------------------------------------------
class _DummyServer(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        self.logger = logging.getLogger('Dummy Server')


# ----------------------------------------------------------------------------------------------------------------------
class BaseRequestHandler(object):

    FORMAT = 'utf-8'

    HEADER_DELIMITER = b'\r\n\r\n'

    # -- kill a connection if no packets were received after 30 seconds. new connections can always be established.
    # -- this keeps the thread buffer clean in the server. Only do this if the keep-alive flag is not set.
    CONNECTION_LIFETIME = 30

    CONNECTION_TIMEOUT = 2

    BLOCKING_SOCKET = False

    # -- transfer speed is a minimum of 16384 bytes per package
    BUFFER_SIZE = 16384

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, marshaller, server=None):
        """
        Base request handler, one of the core frameworks for Clacks. This class is the base class for all
        request handlers, and implements most generic methods used for traffic handling, which mostly consists of
        header parsing and digestion.

        :param marshaller: package marshaller instance for this handler to use
        :type marshaller: BasePackageMarshaller

        :param server: server instance
        :type server: BaseServer

        """
        self.marshaller = marshaller

        # -- in case a handler is ever instantiated but never registered to a server, the DummyServer class
        # -- ensures logging calls don't fail.
        self.server = server or _DummyServer()

        self.timestamps = dict()

        self.socket_is_blocking = self.BLOCKING_SOCKET

        self.connection_keep_alive = dict()

        self.adapters = list()

        # -- list of currently running transactions
        self.transaction_cache = dict()

    # ------------------------------------------------------------------------------------------------------------------
    def _initialize(self):
        # type: () -> bool
        """
        This method is called just before the server is started - this gives handlers, adapters and interfaces the
        opportunity to do some last-minute changes and resource gathering.

        :return: True if successful, if False, the server will not be started.
        :rtype: bool
        """
        self.marshaller.register_handler(self)

        for adapter in self.adapters:
            adapter._initialize()

        return True

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        return self.server.logger

    # ------------------------------------------------------------------------------------------------------------------
    def register_adapter(self, adapter):
        from ..adapters import ServerAdapterBase

        if not isinstance(adapter, ServerAdapterBase):
            raise TypeError('Expected a ServerAdapterBase instance, got %s!' % adapter)

        self.adapters.append(adapter)
        self.marshaller.register_adapter(adapter)

    # ------------------------------------------------------------------------------------------------------------------
    def accept_socket(self, sock):
        # type: (socket.socket) -> tuple
        """
        Accept a socket and return its connection instance and address as a tuple.

        :param sock: socket instance to get a connection from.
        :type sock: socket.socket

        :return: tuple(socket.socket, tuple(host, port))
        :rtype: tuple
        """
        if self.server.stopped:
            raise Exception('Server has stopped - early-outing in handler accept.')

        try:
            connection, address = sock.accept()

        # -- this should not happen unless the server is shutting down, in which case this is fine
        except OSError:
            raise ClacksClientConnectionFailedError(
                'Connection could not be established - server is likely shutting down.'
            )

        connection.setblocking(self.socket_is_blocking)

        # -- only set a timeout when the socket is not blocking
        if not self.socket_is_blocking:
            connection.settimeout(self.CONNECTION_TIMEOUT)

        return connection, address

    # ------------------------------------------------------------------------------------------------------------------
    def register_server(self, server):
        # type: (object) -> None
        """
        Register a server instance to this handler.

        :param server: server instance to register this handler on
        :type server: BaseServer

        :return: None
        """
        if self.server is not None and server is not self.server and not isinstance(self.server, _DummyServer):
            # -- raise this exception for safety - handlers really should not be registered on more than one server.
            raise ValueError(
                f'This handler is already registered to server {self.server}.'
                '\nFor safety purposes, you should not register the same handler on more than one server!'
            )

        self.server = server

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return '%s <%s> Adapters: %s' % (
            self.__class__.__name__,
            self.marshaller.__class__.__name__,
            ' / '.join(str(adapter) for adapter in self.adapters)
        )

    # ------------------------------------------------------------------------------------------------------------------
    def get_outgoing_header_data(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> collections.OrderedDict
        """
        For outgoing payloads, get header data. This can be triggered for both questions _and_ answers, as long as
        the data is outgoing.

        :param transaction_id: transaction ID for the outgoing packet.
        :type transaction_id: str

        :param payload: Package instance, payload of the outgoing packet.
        :type payload: Package

        :param expected_content_length:
        :type expected_content_length: int

        :return: ordered dictionary containing the header data
        :rtype: collections.OrderedDict
        """
        header_data = collections.OrderedDict()
        if payload.header_data:
            header_data.update(payload.header_data)

        try:
            header_data.update(self._get_header_data(transaction_id, payload, header_data))
        except Exception:
            raise ValueError('Could not decode header data {header_data}'.format(header_data=str(header_data)))

        if header_data['Content-Length'] != expected_content_length:
            raise ValueError(
                'Expected content length {expected} does '
                'not match the encoded content length {got}!'.format(
                    expected=expected_content_length,
                    got=header_data['Content-Length']
                )
            )

        return header_data

    # ------------------------------------------------------------------------------------------------------------------
    def _get_header_data(self, transaction_id, payload, header_data):
        # type: (str, Package, collections.OrderedDict) -> collections.OrderedDict
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def decode_question_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        """
        Abstract method for decoding a question header.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param header: byte string containing the question header
        :type header: bytes

        :return: question header as dictionary
        :rtype: dict
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def encode_question_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> bytes
        """
        Encode the question header, returning it as a byte buffer.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param payload:
        :type payload:

        :param expected_content_length:
        :type expected_content_length: int

        :return: the encoded question header as bytes
        :rtype: bytes
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def decode_response_header(self, transaction_id, header):
        # type: (str, bytes) -> dict
        """
        Decode the response header, turning bytes into a consumable dictionary.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param header: byte content of the header
        :type header: bytes

        :return: the decoded response header as a dictionary
        :rtype: dict
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def encode_response_header(self, transaction_id, payload, expected_content_length):
        # type: (str, Package, int) -> bytes
        """
        Encode the response header, returning a byte buffer from the package payload.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param payload: header payload, in bytes
        :type payload: Package

        :param expected_content_length:
        :type expected_content_length: int

        :return: the encoded response header as bytes
        :rtype: bytes
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    def get_content_length(self, transaction_id, payload):
        # type: (str, Package) -> int
        """
        Encode the payload content and return the length of the resulting byte buffer, so that we know how many bytes
        to tell the header to declare for its content-length flag.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param payload: get the length of the given payload content if we were to marshal it, in bytes.
        :type payload: dict

        :return: nr of bytes that would result if we were to marshal the payload to a byte sequence.
        :rtype: int
        """
        bytes_data = self.marshaller.encode_package(transaction_id, payload)
        return len(bytes_data)

    # ------------------------------------------------------------------------------------------------------------------
    def recv_forever(self, connection):
        # type: (socket.socket) -> None
        """
        Open the given socket and infinitely accept packages.

        :param connection: socket instance
        :type connection: socket.socket

        :return: None
        """
        if connection not in self.timestamps:
            self.timestamps[connection] = time.time()

        while True:
            try:
                transaction_id, header_data, data = self._recv(connection, question=True)

            except Exception:
                self.server.logger.exception('Exception raised while receiving package: %s' % traceback.format_exc())
                continue

            if not header_data:
                # -- if this connection is set to keep-alive, do not kill it.
                if self.connection_keep_alive.get(connection, False):
                    time.sleep(0.05)
                    continue

                # -- if we don't want to keep the connection alive, kill it.
                if not self.connection_keep_alive.get(connection, False):
                    connection.close()
                    break

                # -- if the connection has been kept alive for more than the prescribed maximum lifetime, kill it.
                # -- note that this counts of maximum time of inactivity - e.g. since any packages were last received.
                if (time.time() - self.timestamps[connection]) > self.CONNECTION_LIFETIME:
                    connection.close()
                    break

                time.sleep(0.05)
                continue

            # -- reset the timeout
            self.timestamps[connection] = time.time()

            # -- track whether the connection should be kept alive based on the incoming header data
            self.connection_keep_alive[connection] = header_data.get('Connection', '') == 'keep-alive'

            # -- if a package was received, add it to the server queue.
            self.server.add_to_queue(
                handler=self,
                connection=connection,
                transaction_id=transaction_id,
                header_data=header_data,
                data=data
            )

            if not self.connection_keep_alive.get(connection, False):
                return

    # ------------------------------------------------------------------------------------------------------------------
    def receive_response(self, connection):
        # type: (socket.socket) -> typing.Tuple[dict, Response]
        """
        Receive a response from a connection, presuming a question was sent first.

        :param connection: socket connection from which to receive a response.
        :type connection: socket.socket

        :return: tuple of header, response
        :rtype: tuple
        """
        # -- wait until we receive a response
        while True:
            transaction_id, header, data = self._recv(connection, question=False)

            if not header and not data:
                continue

            response = Response.load(header, data)
            response.accept_encoding = header.get('Accept-Encoding', 'text/json')

            return header, response

    # ------------------------------------------------------------------------------------------------------------------
    def _recv_header(self, connection, transaction_id, question):
        # type: (socket.socket, str, bool) -> typing.Tuple[bytes, typing.Union[dict, typing.Any]]
        """
        From a connection instance, receive a header. In the base class this uses the header delimiter method,
        receiving one byte at a time until the last bytes in the sequence match the stored header delimiter.
        For some implementations, this can be overridden if for some reason this behaviour is different.

        :param connection: connection instance to receive the header from.
        :type connection: socket.socket

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param question: if True, the incoming package is a question, otherwise it's a response.
        :type question: bool

        :return: the decoded header package as a dictionary of data
        :rtype: tuple
        """
        for adapter in self.adapters:
            adapter.handler_pre_receive_header(transaction_id)

        header_buffer = b''
        header_received = False

        while not header_received:
            try:
                data = connection.recv(1)
            except Exception:
                break

            # -- if there's no more data to receive, break out.
            if not data:
                break

            header_buffer += data

            # -- most cases should hit this; this tells us the header was received.
            if header_buffer[-4:] == self.HEADER_DELIMITER:
                break

        if not header_buffer:
            return b'', dict()

        header_data = None

        try:
            if question:
                header_data = self.decode_question_header(transaction_id, header_buffer)

            else:
                header_data = self.decode_response_header(transaction_id, header_buffer)
        except Exception:
            pass

        if not header_data:
            raise Exception('Could not decode header %s!' % header_buffer)

        # -- run all handler adapters' "receive header" method on the received data. This is where a header adapter
        # -- may insert information in incoming headers, or trace header data per transaction using the transaction id.
        # -- this last bit is useful when doing things like profiling.
        for adapter in self.adapters:
            adapter.handler_post_receive_header(transaction_id, header_data)

        return header_buffer, header_data

    # ------------------------------------------------------------------------------------------------------------------
    def _recv_content(self, connection, transaction_id, header_data, content_length):
        # type: (socket.socket, str, dict, int) -> tuple
        """
        From a connection instance, receive a content package of a given length.

        :param connection: connection instance to receive the content from.
        :type connection: socket.socket

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param header_data: header data as a dictionary
        :type header_data: dict

        :param content_length: amount of bytes to receive
        :type content_length: int

        :return: tuple of raw_data, decoded_data
        :rtype: tuple
        """
        for adapter in self.adapters:
            adapter.handler_pre_receive_content(transaction_id, header_data)

        _received = 0
        _remaining = content_length

        content_buffer = b''
        while _received < content_length:
            # -- if less data than the packet size is remaining, receive that amount instead
            _buffer = connection.recv(min(self.BUFFER_SIZE, _remaining))
            if not _buffer:
                break

            # -- add to the buffer
            content_buffer += _buffer

            # -- count how many bytes are remaining
            _received += len(_buffer)
            _remaining -= len(_buffer)

        content_data = self.marshaller.decode_package(transaction_id, header_data, content_buffer)

        # -- run all handler adapters' "receive content" method on the received data.
        for adapter in self.adapters:
            adapter.handler_post_receive_content(transaction_id, header_data, content_data)

        return content_buffer, content_data

    # ------------------------------------------------------------------------------------------------------------------
    def _recv(self, connection, question=True):
        # type: (socket.socket, bool) -> tuple
        """
        From a connection instance, receive a package. Can receive either a question or a response.

        :param connection: connection instance to receive package from.
        :type connection: socket.socket

        :param question: If true, treat the incoming content as a Question package. Otherwise, Response.
        :type question: bool

        :return: tuple of (transaction_id, header_data, data)
        :rtype: tuple
        """
        # -- for each transaction, generate a UUID. This Allows us to track all data belonging to it throughout the
        # -- digest of it.
        transaction_id = str(uuid.uuid4())

        header_buffer, header_data = self._recv_header(connection, transaction_id, question)

        content_length = int(header_data.get('Content-Length', '0'))

        if not content_length:
            data = dict()

        else:
            data_buffer, data = self._recv_content(
                connection,
                transaction_id,
                header_data,
                content_length=content_length
            )

            if not data:
                raise ValueError('Could not decode package! Got %s, %s' % (header_data, data_buffer))

        if header_data and data:
            # -- log received data
            self.server.logger.debug('{header_data}...'.format(header_data=str(header_data)))
            self.server.logger.debug('{data}'.format(data=str(data)[:LOG_MSG_LENGTH]))

        return transaction_id, header_data, data

    # ------------------------------------------------------------------------------------------------------------------
    def _compile_buffer(self, transaction_id, package):
        # type: (str, Package) -> bytes
        """
        Marshal a package to a byte sequence.

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param package: package to encode.
        :type package: Package

        :return: compile a package response buffer, triggering the marshalling method.
        :rtype: bytes
        """
        self.server.logger.debug('Building buffer...')

        # -- give adapters the chance to trigger any callbacks or make changes to package pre-compile
        for adapter in self.adapters:
            adapter.handler_pre_compile_buffer(transaction_id, package)

        bytes_data = None
        try:
            bytes_data = self.marshaller.encode_package(transaction_id, package)
        except Exception:
            self.server.logger.error(traceback.format_exc())

        if not bytes_data:
            bytes_data = self.marshaller.encode_package(
                transaction_id,
                Response(
                    response=HandlerErrors.BAD_CONTENT % package.payload,
                    code=ReturnCodes.MARSHAL_ERROR,
                )
            )

        if not isinstance(bytes_data, bytes):
            raise TypeError('Marshaller %s did not encode package as bytes!' % self.marshaller)

        expected_content_length = len(bytes_data)

        if isinstance(package, Question):
            header = self.encode_question_header(transaction_id, package, expected_content_length)

        elif isinstance(package, Response):
            header = self.encode_response_header(transaction_id, package, expected_content_length)

        else:
            raise ValueError(
                'Package is neither Question nor Response, or an inheritor thereof. Got %s' % package.__class__.__name__
            )

        if not isinstance(header, bytes):
            raise TypeError('handler %s did not encode header as bytes!' % self)

        _buffer = b''

        # -- build the buffer
        _buffer += header
        _buffer += self.HEADER_DELIMITER
        _buffer += bytes_data

        # -- give adapters the chance to trigger any callbacks or make changes to packages pre-compile
        for adapter in self.adapters:
            adapter.handler_post_compile_buffer(transaction_id, package)

        return _buffer

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, connection, transaction_id, package):
        # type: (socket.socket, str, Package) -> None
        """
        Send a package on a connection instance.

        :param connection: connection to send package to.
        :type connection: socket.socket

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param package: package to send.
        :type package: Package

        :return: None
        """
        if not isinstance(package, Package):
            raise TypeError('Cannot send pure data - all packages must inherit from Package! Got %s' % type(package))

        _buffer = self._compile_buffer(transaction_id, package)

        # -- send the buffer
        connection.sendall(_buffer)

        self.server.logger.debug('Sent %s bytes' % len(_buffer))

    # ------------------------------------------------------------------------------------------------------------------
    def respond(self, connection, transaction_id, response):
        # type: (socket.socket, str, Response) -> None
        """
        Respond to a question with a given response.

        :param connection: connection instance to send the response to.
        :type connection: socket.socket

        :param transaction_id: UUID that uniquely identifiers the transaction this header belongs to.
        :type transaction_id: str

        :param response: the response instance to marshal and send.
        :type response: Response

        :return: None
        """
        # -- give adapters the chance to trigger any callbacks or make changes to packages pre-send
        for adapter in self.adapters:
            adapter.handler_pre_respond(connection, transaction_id, response)

        # -- log response, so we know what came out (and if we got stuck somewhere)
        self.logger.debug('Response: {response}...'.format(response=str(response)[:LOG_MSG_LENGTH]))

        try:
            self.send(connection, transaction_id=transaction_id, package=response)

        except socket.error:
            self.logger.exception('Could not send response %s' % response)

        # -- give adapters the chance to trigger any callbacks or make changes to packages post-send
        for adapter in self.adapters:
            adapter.handler_post_respond(connection, transaction_id, response)
