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
import socket

from ..base import ServerInterface
from ..constants import register_server_interface_type
from ...command import private, returns, takes
from ...utils import quick_listening_socket


class FileIOServerInterface(ServerInterface):
    """
    File I/O Interface for transferring files between proxies and servers. This is the Server side.
    """

    key = 'file_io'

    layer = 'server'

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        super(FileIOServerInterface, self).__init__()
        self.file_cache = dict()

        self.cache_dir = os.path.join(os.getenv('TEMP'), 'FileIOServerInterfaceFileCache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.recv_sockets = dict()

    # ------------------------------------------------------------------------------------------------------------------
    @private
    def acquire_file_handle(self, file_name):
        # type: (str) -> str
        file_path = os.path.join(self.cache_dir, file_name)

        # -- the user may provide extra slashes, so we want those to be directories.
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        # -- file system file path the server will store this in - the user will just get the file name back.
        self.file_cache[file_name] = file_path

        return file_path

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'file_name': str})
    @returns(str)
    def get_server_file_path(self, file_name):
        # type: (str) -> str
        return self.file_cache.get(file_name)

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'server_file': str})
    @returns(str)
    def get_server_file_handle(self, server_file):
        # type: (str) -> str
        result = server_file.replace(self.cache_dir, '').lstrip('/').lstrip('\\')
        if result not in self.file_cache:
            self.file_cache[result] = server_file
        return result

    # ------------------------------------------------------------------------------------------------------------------
    @returns(None)
    def open_socket(self):
        # type: () -> tuple
        s = quick_listening_socket(socket.gethostbyname(socket.gethostname()), 0)
        address = s.getsockname()
        self.recv_sockets[address] = s
        return address

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'address': tuple, 'file_name': str})
    @returns(str)
    def store_file(self, address, file_name):
        # type: (tuple, str) -> str
        address = (address[0], address[1])
        s = self.recv_sockets.get(address)
        if not s:
            raise ValueError('No socket listening on %s!' % str(address))

        conn, addr = s.accept()
        conn.settimeout(0.25)

        file_path = self.acquire_file_handle(file_name)
        if not file_path:
            raise ValueError('Could not acquire file handle on %s' % file_name)

        self.server.logger.info('Receiving file on socket connection %s' % str(s.getsockname()))

        # -- this is a blind receive; we don't know how many bytes are coming, because it defeats the purpose, as we
        # -- are assuming a potentially huge amount. More than can fit into the RAM of the machine. Therefore, we
        # -- keep receiving until there's nothing left.
        buf_size = 16384
        received = 0
        with open(file_path, 'w+b') as handle:
            while True:
                # -- keep receiving until there's nothing left.
                try:
                    chunk = conn.recv(buf_size)
                    if not chunk:
                        break
                    handle.write(chunk)
                    received += len(chunk)
                except socket.timeout:
                    break

        self.server.logger.info('Received %s bytes' % received)
        handle.close()

        # -- close sockets and remove them
        conn.close()
        s.close()
        del self.recv_sockets[address]

        return file_name

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'address': tuple, 'file_name': str})
    @returns(str)
    def retrieve_file(self, address, file_name):
        # type: (tuple, str) -> str
        file_path = self.file_cache.get(file_name)
        if not file_path:
            return ''

        if not os.path.exists(file_path):
            return ''

        # -- acquire a read handle on the file
        file_path = self.acquire_file_handle(file_name)

        s = socket.socket()
        s.connect((address[0], address[1]))

        # -- this protocol creates a "blind send / receive" transaction, which assumes that the data size is too big
        # -- to pre-determine the length of. Hence we simply stream the entire contents to the socket and assume
        # -- the receiving socket knows what to do with it.
        buf_size = 16384
        sent = 0
        with open(file_path, 'rb') as handle:
            while True:
                _slice = handle.read(buf_size)
                if not _slice:
                    break
                s.sendall(_slice)
                sent += len(_slice)

        self.server.logger.info('Sent %s bytes' % sent)

        # -- close the socket.
        s.close()

        return file_name

    # ------------------------------------------------------------------------------------------------------------------
    @takes({'file_name': str})
    @returns(None)
    def remove_file(self, file_name):
        # type: (str) -> None
        file_path = self.file_cache.get(file_name)
        if not file_path:
            return None

        if not os.path.exists(file_path):
            return None

        os.unlink(file_path)
        del self.file_cache[file_name]


register_server_interface_type('file_io', FileIOServerInterface)
