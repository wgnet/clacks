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
import sys
import time
import clacks
import unittest


# -- python 3 migrates StringIO to io
if sys.version_info.major == 3:
    import io
    _StringIO = io

if sys.version_info.major == 2:
    import StringIO
    _StringIO = StringIO


# -- python 3 does not have "unicode", but it does have "bytes".
_unicode = bytes
if sys.version_info.major == 2:
    _unicode = unicode


# ----------------------------------------------------------------------------------------------------------------------
class TestSocketStreamer(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_streaming_socket(self):
        host, port = 'localhost', clacks.get_new_port('localhost')
        address = (host, port)

        broadcaster = clacks.core.utils.StreamingSocket(host, port)

        stream = _StringIO.StringIO()
        listener = clacks.core.utils.StreamingSocketReceiver(address, stream=stream)

        nr_iterations = 1

        pattern = b'Hello world'

        for i in range(nr_iterations):
            broadcaster.write(pattern)

        time.sleep(2)

        value = stream.getvalue()

        broadcaster.stop()
        listener.stop()

        # -- check that all the messages made it through
        assert len(value) == (len(pattern) * nr_iterations)
