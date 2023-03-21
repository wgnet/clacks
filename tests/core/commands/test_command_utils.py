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
import unittest
from clacks.core.utils import is_key_legal


# ----------------------------------------------------------------------------------------------------------------------
class TestCommandUtils(unittest.TestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_is_command_key_legal(self):
        assert is_key_legal(None) is False
        assert is_key_legal(0) is False
        assert is_key_legal(False) is False
        assert is_key_legal(True) is False
        assert is_key_legal('foo') is True
        assert is_key_legal('12345') is False
        assert is_key_legal('foo_bar') is True
