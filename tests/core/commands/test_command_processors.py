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
import clacks
from clacks.tests import ClacksTestCase

from clacks.core.command import process_arguments, process_result
from clacks.core.command.result_processors import return_as_json
from clacks.core.command.arg_processors import auto_strip_args, strip_args
from clacks.core.command.arg_processors import enforce_argument_types, kwargs_from_json
from clacks.core.command.arg_processors import example_arg_processor, auto_convert_arguments
from clacks.core.command.result_processors import enforce_return_type, example_result_processor


# -- python 3 does not have "unicode", but it does have "bytes".
_unicode = bytes
if sys.version_info.major == 2:
    _unicode = unicode


# ----------------------------------------------------------------------------------------------------------------------
class TestCommandProcessors(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_auto_strip_args(self):
        @process_arguments([auto_strip_args])
        def testing_auto_strip_args(a, b, c=None):
            return a, b, c

        self.server.register_command('test_auto_strip_args', testing_auto_strip_args)

        response = self.client.test_auto_strip_args(0, 1, d='d').response

        if len(response) != 3:
            self.fail()

        # -- expected result from this method is that the 'd' argument has been stripped, and the 'c' argument
        # -- returns None
        if response != (0, 1, None):
            self.fail()

    # ------------------------------------------------------------------------------------------------------------------
    def test_strip_args(self):
        @process_arguments([strip_args])
        def testing_strip_arguments(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_strip_args', testing_strip_arguments)

        response = self.client.test_strip_args(0, 1, d='d').response

        args, kwargs = response

        if len(args):
            self.fail()

        if kwargs:
            self.fail()

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor(self):
        def bad_command_processor(server_command, *args, **kwargs):
            raise Exception

        @process_arguments([bad_command_processor])
        def foobar(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor', foobar)

        try:
            self.client.foobar()
            self.fail()
        except Exception:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor_fake_tuple(self):
        def bad_command_processor_fake_tuple(server_command, *args, **kwargs):
            return None, None

        @process_arguments([bad_command_processor_fake_tuple])
        def test_bad_command_processor_fake_tuple(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor_fake_tuple', test_bad_command_processor_fake_tuple)

        try:
            self.client.test_bad_command_processor_fake_tuple()
            self.fail()
        except Exception:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_result_processor(self):
        def bad_result_processor(server_command, result):
            raise Exception()

        @process_result([bad_result_processor])
        def test_bad_result_processor(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_result_processor', test_bad_result_processor)

        try:
            self.client.test_bad_result_processor()
            self.fail()
        except Exception:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_example_processors(self):
        @process_arguments(['example_arg_processor'])
        @process_result(['example_result_processor'])
        def command_test(value):
            return value

        self.server.register_command('test', command_test)

        assert self.client.test('foo').response == 'foo'

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor_not_a_tuple(self):
        def bad_command_processor_not_a_tuple(server_command, *args, **kwargs):
            return None

        @process_arguments([bad_command_processor_not_a_tuple])
        def test_bad_command_processor_not_a_tuple(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor_not_a_tuple', test_bad_command_processor_not_a_tuple)

        try:
            self.client.test_bad_command_processor_not_a_tuple()
            self.fail()
        except clacks.errors.ClacksBadArgProcessorOutputError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor_wrong_length(self):
        def bad_command_processor_wrong_length(server_command, *args, **kwargs):
            return None, None, None

        @process_arguments([bad_command_processor_wrong_length])
        def test_bad_command_processor_wrong_length(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor_wrong_length', test_bad_command_processor_wrong_length)

        try:
            self.client.test_bad_command_processor_wrong_length()
            self.fail()
        except clacks.errors.ClacksBadArgProcessorOutputError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor_kwargs(self):
        def bad_command_processor_kwargs(server_command, *args, **kwargs):
            return args, None

        @process_arguments([bad_command_processor_kwargs])
        def test_bad_command_processor_kwargs(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor_kwargs', test_bad_command_processor_kwargs)

        try:
            self.client.test_bad_command_processor_kwargs()
            self.fail()
        except clacks.errors.ClacksBadArgProcessorOutputError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_bad_command_processor_args(self):
        def bad_command_processor_args(server_command, *args, **kwargs):
            return None, kwargs

        @process_arguments([bad_command_processor_args])
        def test_bad_command_processor_args(*args, **kwargs):
            return args, kwargs

        self.server.register_command('test_bad_command_processor_args', test_bad_command_processor_args)

        try:
            self.client.test_bad_command_processor_args()
            self.fail()
        except clacks.errors.ClacksBadArgProcessorOutputError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_auto_convert_arguments(self):
        @process_arguments([auto_convert_arguments])
        @clacks.decorators.takes(
            dict(
                integer=int,
                floating_point=float,
                string=str,
                boolean=bool,
                list_value=list
            )
        )
        def _test_auto_convert_arguments(
                integer=None,
                floating_point=None,
                string=None,
                boolean=None,
                list_value=None
        ):
            return integer, floating_point, string, boolean, list_value

        @process_arguments([auto_convert_arguments])
        @clacks.decorators.takes(
            dict(
                integer=int,
                string=str,
                list_value=list
            )
        )
        def _test_auto_convert_arguments_partially_decorated(
                integer=None,
                floating_point=None,
                string=None,
                boolean=None,
                list_value=None
        ):
            return integer, floating_point, string, boolean, list_value

        @process_arguments([auto_convert_arguments])
        def _test_auto_convert_arguments_undecorated(
                integer=None,
                floating_point=None,
                string=None,
                boolean=None,
                list_value=None
        ):
            return integer, floating_point, string, boolean, list_value

        self.server.register_command(
            'test_auto_convert_arguments',
            _test_auto_convert_arguments
        )

        self.server.register_command(
            'test_auto_convert_arguments_partially_decorated',
            _test_auto_convert_arguments_partially_decorated
        )

        self.server.register_command(
            'test_auto_convert_arguments_undecorated',
            _test_auto_convert_arguments_undecorated
        )

        _integer, _floating_point, _string, _boolean, _list_value = self.client.test_auto_convert_arguments(
            integer=5.0,
            floating_point=2,
            string=True,
            boolean='',
            list_value='four'
        ).response

        assert isinstance(_integer, int)
        assert isinstance(_floating_point, float)
        assert isinstance(_string, (str, _unicode))
        assert isinstance(_boolean, bool)
        assert isinstance(_list_value, list)

        # -- only for coverage
        response = self.client.test_auto_convert_arguments_partially_decorated(
            integer=5.0,
            floating_point=2,
            string=True,
            boolean='',
            list_value='four'
        ).response

        # -- only for coverage
        response = self.client.test_auto_convert_arguments_undecorated(
            integer=5.0,
            floating_point=2,
            string=True,
            boolean='',
            list_value='four'
        ).response

        try:
            response = self.client.test_auto_convert_arguments(
                integer=['cannot convert this to integer'],
            ).response
            self.fail()
        except TypeError:
            pass

        try:
            response = self.client.test_auto_convert_arguments(
                floating_point='cannot convert this to floating point',
            ).response
            self.fail()
        except TypeError:
            pass

        try:
            response = self.client.test_auto_convert_arguments(
                list_value=None,
            ).response
            self.fail()
        except TypeError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_enforce_argument_types(self):
        @process_arguments([enforce_argument_types])
        @clacks.decorators.takes(
            dict(
                integer=int,
                floating_point=float,
                string=(str, _unicode),
                boolean=bool,
                list_value=list
            )
        )
        def _test_enforce_argument_types(
                integer=None,
                floating_point=None,
                string=None,
                boolean=None,
                list_value=None
        ):
            return integer, floating_point, string, boolean, list_value

        @process_arguments([enforce_argument_types])
        def _test_enforce_argument_types_undecorated(*args, **kwargs):
            return args, kwargs

        @process_arguments([enforce_argument_types])
        @clacks.decorators.takes(
            dict(
                integer=int,
                string=(str, _unicode),
                list_value=list
            )
        )
        def _test_enforce_argument_types_partially_decorated(
                integer=None,
                floating_point=None,
                string=None,
                boolean=None,
                list_value=None
        ):
            return integer, floating_point, string, boolean, list_value

        self.server.register_command(
            'test_enforce_argument_types',
            _test_enforce_argument_types
        )
        self.server.register_command(
            'test_enforce_argument_types_undecorated',
            _test_enforce_argument_types_undecorated
        )

        self.server.register_command(
            'test_enforce_argument_types_partially_decorated',
            _test_enforce_argument_types_partially_decorated
        )

        # -- this should not fail; in undecorated methods, the "enforce argument types" decorator does not do anything.
        response = self.client.test_enforce_argument_types_undecorated(foo='bar').response

        response = self.client.test_enforce_argument_types_partially_decorated(
            integer=1,
            floating_point=5.0,
            string='None',
            boolean=False,
            list_value=['list']
        ).response

        # -- this should pass, as in this test, floating_point and boolean are not decorated and so are not enforced.
        self.client.test_enforce_argument_types_partially_decorated(
            integer=1,
            floating_point=False,
            string='None',
            boolean=None,
            list_value=['list']
        )

        try:
            self.client.test_enforce_argument_types(integer=5.0)
            self.fail()
        except TypeError:
            pass

        try:
            self.client.test_enforce_argument_types(floating_point=1)
            self.fail()
        except TypeError:
            pass

        try:
            self.client.test_enforce_argument_types(string=5.0)
            self.fail()
        except TypeError:
            pass

        try:
            self.client.test_enforce_argument_types(boolean=None)
            self.fail()
        except TypeError:
            pass

        try:
            self.client.test_enforce_argument_types(list_value=None)
            self.fail()
        except TypeError:
            pass

        self.client.test_enforce_argument_types(integer=5)
        self.client.test_enforce_argument_types(floating_point=5.0)
        self.client.test_enforce_argument_types(string='5')
        self.client.test_enforce_argument_types(boolean=False)
        self.client.test_enforce_argument_types(list_value=['list'])

    # ------------------------------------------------------------------------------------------------------------------
    def test_kwargs_from_json(self):
        @process_arguments([kwargs_from_json])
        def _test_kwargs_from_json(**kwargs):
            return kwargs

        self.server.register_command('kwargs_from_json', _test_kwargs_from_json)

        # -- this decorator will convert json string input to keyword argument input
        response = self.client.kwargs_from_json('{"foo": "bar"}').response

        try:
            # -- this will fail as kwargs_from_json only takes 1 argument
            response = self.client.kwargs_from_json('{"foo": "bar"}', '{"foo": "bar"}')
            self.fail()
        except ValueError:
            pass

        try:
            # -- this will fail as kwargs_from_json only takes 1 positional argument, no kwargs
            response = self.client.kwargs_from_json('{"foo": "bar"}', foo='bar')
            self.fail()
        except ValueError:
            pass

        try:
            # -- this will fail as this is not JSON compatible formatting.
            response = self.client.kwargs_from_json('some value')
            self.fail()
        except ValueError:
            pass

        assert response['foo'] == 'bar'

    # ------------------------------------------------------------------------------------------------------------------
    def test_enforce_return_type(self):
        @process_result([enforce_return_type])
        @clacks.decorators.returns(dict)
        def returns_dict(**kwargs):
            return kwargs

        @process_result([enforce_return_type])
        @clacks.decorators.returns(dict)
        def returns_list(**kwargs):
            return list(kwargs.keys())

        self.server.register_command('returns_dict', returns_dict)
        self.server.register_command('returns_list', returns_list)

        # -- this decorator will convert json string input to keyword argument input
        response = self.client.returns_dict(foo='bar').response
        assert response['foo'] == 'bar'

        try:
            response = self.client.returns_list(foo='bar').response
            self.fail()
        except TypeError:
            pass

    # ------------------------------------------------------------------------------------------------------------------
    def test_return_as_json(self):
        @clacks.decorators.process_result([return_as_json])
        def returns_as_json(**kwargs):
            return kwargs

        @clacks.decorators.process_result([return_as_json])
        def returns_as_json_bad(**kwargs):
            return None

        self.server.register_command('return_as_json', returns_as_json)
        self.server.register_command('return_as_json_bad', returns_as_json_bad)

        response = self.client.return_as_json(foo='bar').response
        assert response == '{"foo": "bar"}'

        try:
            self.client.return_as_json_bad(foo='bar')
            self.fail()
        except ValueError:
            pass
