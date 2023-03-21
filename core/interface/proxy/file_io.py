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
import threading

from ..base import ServerInterface
from ..constants import register_proxy_interface_type
from ...utils import quick_listening_socket


class FileIOServerProxyInterface(ServerInterface):
    """
    File I/O Interface for transferring files between proxies and servers. This is the Proxy (Client) side.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def transfer_file(self, file_path, server_file_name):
        # type: (str, str) -> str
        """
        Transfers the contents of a file to the server machine, and returns a server-local file path that can be used
        later as a function argument to perform operations on the file in question.

        The receiving server must implement the FileIOServerInterface interface for this method to work.

        :param file_path: the absolute file path to transfer.
        :type file_path: str

        :param server_file_name: the file name of the file on the server (functions relatively)
        :type server_file_name: str

        :return: the server-local file path the file was stored in
        :rtype: str
        """
        if not os.path.exists(file_path):
            raise ValueError('File path %s does not exist!' % file_path)

        address = self.server.open_socket().response

        if not address:
            raise ValueError('Could not acquire address from the server!')

        s = socket.socket()
        s.connect((address[0], address[1]))

        def _send_file(*args):
            # -- stream the data in chunks to our receiving socket
            buff_size = 16384
            with open(file_path, 'rb') as fp:
                while True:
                    chunk = fp.read(buff_size)
                    if not chunk:
                        break
                    s.sendall(chunk)
            fp.close()

        # -- send the data in a thread
        thread = threading.Thread(target=_send_file)
        thread.daemon = True
        thread.start()

        # -- wait for the result
        result = self.server.store_file(tuple(address), server_file_name).response

        # -- close the socket
        s.close()

        # -- return the file name
        return result

    # ------------------------------------------------------------------------------------------------------------------
    def download_file(self, file_name, output_file_name):
        # type: (str, str) -> str
        """
        Retrieve file contents from the server, using its file name lookup. This will begin streaming the file
        contents to a new port, which will stream the content directly into the provided output file name.

        :param file_name: the server key for the file name to download
        :type file_name: str

        :param output_file_name: the output file name on local disk to store the file in
        :type output_file_name: str

        :return: the file name on disk where the data was written to
        :rtype: str
        """
        s = quick_listening_socket()
        host, port = s.getsockname()

        def retrieve():
            self.server.retrieve_file((host, port), file_name)

        thread = threading.Thread(target=retrieve)
        thread.daemon = True
        thread.start()

        conn, _ = s.accept()
        conn.settimeout(3)

        buff_size = 16384

        # -- write the contents directly to the file, don't store them in memory
        # -- this is a blind receive, we do not know how many bytes are coming!
        with open(output_file_name, 'w+b') as file_stream:
            while True:
                try:
                    buff = conn.recv(buff_size)
                    if not buff:
                        break
                    file_stream.write(buff)
                except socket.timeout:
                    break
        file_stream.close()

        # -- now that we're done, close the connection.
        s.close()
        conn.close()

        return output_file_name


register_proxy_interface_type('file_io', FileIOServerProxyInterface)
