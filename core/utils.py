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
import socket
import sys
import threading
import time

LEGAL_TOKENS = 'abcdefghijklmnopqrstuvwxyz_'

# -- python 3 does not have "unicode", but it does have "bytes".
_unicode = bytes
if sys.version_info.major == 2:
    _unicode = unicode


# ----------------------------------------------------------------------------------------------------------------------
def is_key_legal(key):
    """
    Return True if the given command key/alias is legal for use in servers.

    :param key: the key to check
    :type key: str

    :return: True if the given key is legal
    :rtype: bool
    """
    # type (str) -> bool
    if key is None:
        return False

    if not isinstance(key, (str, _unicode)):
        return False

    for character in list(key.lower()):
        if character.lower() not in LEGAL_TOKENS:
            return False

    return True


# ----------------------------------------------------------------------------------------------------------------------
def get_new_port(host='localhost'):
    # type: (str) -> int
    """
    Automatically generate a new unoccupied port number.

    :param host: the host to get the new port number on
    :type host: str

    :return: the port number
    :rtype: int
    """
    s = socket.socket()
    s.bind((host, 0))
    host, port = s.getsockname()
    s.close()
    return port


# ----------------------------------------------------------------------------------------------------------------------
def quick_listening_socket(host=None, port=0):
    # type: (str, int) -> socket.socket
    """
    Create a new socket, set it to blocking and start listening on it.

    :param host: the host to create the socket on
    :type host: str

    :param port: the port to listen on. Defaults to 0, which will assign a random unassigned port.
    :type port: int

    :return: the socket
    :rtype: socket.socket
    """
    host = host or socket.gethostbyname(socket.gethostname())

    s = socket.socket()
    s.setblocking(1)
    s.bind((host, port))
    s.listen(1)

    return s


# ----------------------------------------------------------------------------------------------------------------------
def one_off_send(address, payload):
    # type: (tuple, str) -> None
    """
    Send a payload to the given address, assuming a socket is listening on the other end.

    This works with a simple protocol, sending a 16-byte header that just contains an integer indicating the payload
    size in bytes. The assumption is that the receiving end respects this protocol, such as for example the
    "one_off_receive" method.

    :param address: tuple (host, port)
    :type address: tuple

    :param payload: string-compatible payload to send
    :type payload: str

    :return: None
    """
    s = socket.socket()
    s.connect(address)

    payload = str(payload)

    header = b'%s' % len(payload)
    header += b' ' * (16 - len(payload))

    s.send(header)
    s.send(payload)


# ----------------------------------------------------------------------------------------------------------------------
def one_off_receive(_socket, stream):
    # type: (socket.socket, (file, object)) -> file
    """
    From a listening socket accepting connections, get the next incoming payload according to the standard protocol.

    The protocol assumes a 16-byte header is sent, containing a single integer declaring the size of the incoming
    payload.

    :param _socket: a listening socket ready to accept connections.
    :type _socket: socket.socket

    :param stream: file or StringIO object that can be written to. This way this method can be used to write to disk
    :type stream: file, io.StringIO

    :return: the received payload
    :rtype: the file stream
    """
    conn, addr = _socket.accept()

    start = time.time()
    content_length = None
    while not content_length:
        if time.time() - start > 30:
            break

        content_length = conn.recv(16)
        if not content_length:
            time.sleep(0.1)
            continue

        content_length = int(content_length.strip())

    # -- now that we know how many bytes to receive, begin receiving them in slices
    # -- ensuring that we don't max out the socket capacity (as that strains the system)
    remaining = content_length
    buff_size = 16384
    while remaining > 0:
        _slice = conn.recv(min(buff_size, remaining))
        remaining -= len(_slice)
        stream.write(str(_slice))

    conn.close()

    # -- reset the stream to 0 so that when we call "read()" we actually get something back.
    # -- this is a byte stream thing; when you write to a stream, its "cursor" is set to the last byte.
    # -- this means that if you call "read()" on this without calling "seek(0)" first, you will begin reading
    # -- from the last byte that was written, which of course will not be anything and will therefore return empty.
    stream.seek(0)

    return stream


# ----------------------------------------------------------------------------------------------------------------------
class StreamingSocket(object):
    """
    Streaming socket, implemented like a super-simple mini-server and with methods to behave as a stream-like IO object.
    This class must be instanced with a host, port argument combo, and expects to have connections listening to it.
    It works by accumulating a buffer, and, while other sockets are listening to it, by broadcasting the buffer contents
    to all listeners.

    While nothing is listening to it, this class will continue to empty its buffer; any new listeners will not get the
    buffer contents retroactively, rather they will start receiving buffer output from the time when they started
    listening.

    The use case for this class is to be able to implement a remote stdout console for server instances.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, host, port):
        # type: (str, int) -> None
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.setblocking(True)
        self.socket.listen(5)

        self.buffer = b''
        self.packet_size = 16384
        self.stopped = False

        self.connections = dict()
        self.needs_cleaning = False

        self.accept_thread = threading.Thread(target=self.accept)
        self.accept_thread.daemon = True
        self.accept_thread.start()

        self.work_thread = threading.Thread(target=self.work)
        self.work_thread.daemon = True
        self.work_thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        self.stopped = True

    # ------------------------------------------------------------------------------------------------------------------
    def accept(self):
        while not self.stopped:
            conn, address = self.socket.accept()
            self.connections[address] = conn

    # ------------------------------------------------------------------------------------------------------------------
    def clean(self):
        needs_removal = list()

        for key in self.connections:
            try:
                self.connections[key].getsockname()
            except Exception:
                needs_removal.append(key)

        for key in needs_removal:
            del self.connections[key]

        self.needs_cleaning = False

    # ------------------------------------------------------------------------------------------------------------------
    def work(self):
        while not self.stopped:
            if not self.buffer:
                time.sleep(0.5)
                continue

            packet = None

            if len(self.buffer) >= self.packet_size:
                packet = self.buffer[:self.packet_size]
                self.buffer = self.buffer[self.packet_size:]

            elif len(self.buffer) < self.packet_size:
                packet = self.buffer[:]
                self.buffer = b''

            if not packet:
                time.sleep(0.5)
                continue

            for conn in self.connections.values():
                try:
                    conn.sendall(packet)
                except Exception:
                    self.needs_cleaning = True

            if self.needs_cleaning:
                self.clean()

    # ------------------------------------------------------------------------------------------------------------------
    def write(self, buf):
        # type: (str) -> None
        if isinstance(buf, str):
            buf = _unicode(buf, 'utf-8')
        if not isinstance(buf, (_unicode)):
            raise ValueError('Streaming socket buffer input must be bytes!')
        self.buffer += buf

    # ------------------------------------------------------------------------------------------------------------------
    def getvalue(self):
        return self.buffer


# ----------------------------------------------------------------------------------------------------------------------
class StreamingSocketReceiver(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, address, stream):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect(address)
        self.socket.setblocking(True)

        self.stopped = False

        self.packet_size = 16384

        self.stream = stream

        self.thread = threading.Thread(target=self.recv)
        self.thread.daemon = True
        self.thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        self.stopped = True

    # ------------------------------------------------------------------------------------------------------------------
    def recv(self):
        while not self.stopped:
            packet = self.socket.recv(self.packet_size)
            self.stream.write(packet.decode('utf-8'))
