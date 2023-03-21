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
import sys
from clacks.tests import ClacksTestCase


# -- python 3 does not have "unicode", but it does have "bytes".
_unicode = bytes
if sys.version_info.major == 2:
    _unicode = unicode


# ----------------------------------------------------------------------------------------------------------------------
class TestServerTypes(ClacksTestCase):

    rebuild_server = True

    # ------------------------------------------------------------------------------------------------------------------
    def setUp(self):
        test_file = 'test.bin'
        # -- make a big file

        buff = '--' * 50000000
        print('making a big file: 100 megabytes')
        with open(test_file, 'w+b') as fp:
            fp.write(_unicode(buff, encoding='utf-8'))
        fp.close()

    # ------------------------------------------------------------------------------------------------------------------
    def tearDown(self):
        try:
            os.unlink('test.bin')
        except:
            pass

        try:
            os.unlink('test_copy.bin')
        except:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_big_file(self):
        # -- transfer the file to the server, so it can do something with it
        print('Uploading file to server')
        server_file = self.client.transfer_file('test.bin', 'test.bin')

        # -- now retrieve the file from the server
        print('Downloading file from server')
        self.client.download_file(server_file, 'test_copy.bin')

        print('reading files')
        with open('test.bin') as fp:
            a = fp.read()
        fp.close()

        with open('test_copy.bin') as fp:
            b = fp.read()
        fp.close()

        print('Comparing download to upload')
        assert a == b, 'copy didn\'t make it back intact!'
