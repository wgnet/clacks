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
from clacks.tests import ClacksTestCase


def foo():
    print('bar')


def echo(value=None, other=None):
    return value


# ----------------------------------------------------------------------------------------------------------------------
class TestServerCommands(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_get_doc(self):
        def doc_test():
            """FooBar"""
            return True

        command = clacks.ServerCommand(interface=self.interface, _callable=doc_test)
        value = command.docstring
        assert value == 'FooBar'
        value = command.__doc__()
        assert value == 'FooBar'

    # ------------------------------------------------------------------------------------------------------------------
    def test_verbose_help(self):
        def doc_test():
            """FooBar"""
            return True

        command = clacks.ServerCommand(interface=self.interface, _callable=doc_test)
        help(command)

    # ------------------------------------------------------------------------------------------------------------------
    def test_create_bad_command(self):
        try:
            command = clacks.ServerCommand(interface=self.interface, _callable=None)
            self.fail()
        except ValueError:
            pass

        def foo():
            print('bar')

        try:
            command = clacks.ServerCommand(interface=None, _callable=foo)
            self.fail()
        except ValueError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_command_key(self):
        try:
            self.server.register_command('bad command key', foo)
            self.fail()
        # -- this should raise a ValueError
        except TypeError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_register_bad_command_value(self):
        try:
            self.server.register_command('key', None)
            self.fail()
        # -- this should raise a ValueError
        except TypeError:
            pass
