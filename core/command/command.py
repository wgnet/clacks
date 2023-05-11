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

ServerCommand
=============

This is purely a utility class - servers will take standard callables and register them using the function name,
but these are considered "naked" as the server knows nothing about them.

The `ServerCommand` class attempts to make this easier by allowing a user to register decorated method that are
considered "annotated" using the decorators provided by `Clacks`.

The `ServerCommand` is the only way a server knows how to run a method. As such, the more information a developer
provides about a command, the better, as the server will be able to provide more intelligent responses.

There are two distinct ways to invoke a `ServerCommand`:

The most common of those 2 ways is through the `digest` method, which is invoked by the `ServerBase` class when a
command is removed from the queue and executed.
The server queue _always_ assumes that every item in the queue is a command meant to be executed.

The second, less common way to invoke a `ServerCommand` is to simply call it like a function. As this class implements
the __call__ magic method, all `ServerCommand` instances function like a thin wrapper around the function they decorate.

There are four distinct phases to a server command's execution process; however, when invoked like a common function,
only one of these actually triggers: the invocation of the decorated method. It is therefore strongly advised not to
invoke `ServerCommand` instances directly, but rather to let the server handle all command executions.

The four phases of a `ServerCommand`'s execution are:

Pre-Process
-----------

This phase consumes any header data that was passed along with the server `Question` instance, and sees if it contains
a "kwargs" entry. If this is the case, the command will update any keyword arguments it had before with these new ones.

Argument Processing
-------------------

This phase takes any positionals and keyword arguments that were found, and runs them through the registered argument
processors for this command.

This allows a user to modify incoming data, _before_ it gets to the method itself. This is supremely useful for cases
like enforcement of argument types, or conversion from one data type to another for special use cases, like web servers,
for example, which get a JSON string as input. Argument processors in this case can be used to turn a simple JSON string
into a set of keyword arguments, allowing for the method implementation to be the same between different handler types,
just exposing different server command variations.

**Note**:

Argument processors are expected to return a tuple of (list, dict) for positional and keyword arguments respectively.
Argument processors receive three values as arguments:

- the server command instance invoking them
- positional arguments ( as *args )
- keyword arguments ( as **kwargs )

An example implementation would be as follows:

    >>> def example_arg_processor(server_command, *args, **kwargs):
    ...    return args, kwargs

Execution
---------

This step takes the processed positional and keyword arguments and runs them through the decorated method.

Result Processing
-----------------

`Result Processors take the output value of the executed method and are allowed to change it or analyze it. This has
many uses, including input/output standardization for different server types that use the same method. (same use case
as argument processors)

    >>> def example_result_processor(server_command, result):
    ...    return result

Response
--------

Once all information is gathered, including final return value, any exceptions encountered, and information on execution
time, the Response package is constructed and returned to the server for handling.

"""
import logging
import collections

from ..errors import ReturnCodes
from ..package import Question, Response
from ..errors import ClacksBadCommandArgsError
from ..errors import ClacksCommandIsPrivateError
from ..errors import ClacksBadArgProcessorOutputError
from ..errors import ClacksCommandUnexpectedReturnValueError


# ----------------------------------------------------------------------------------------------------------------------
class ServerCommand(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(
            self,
            interface,
            _callable,
            private=False,
            arg_defaults=None,
            arg_types=None,
            return_type=object,
            help_obj=None,
            aliases=None,
            former_aliases=None,
            arg_processors=None,
            result_processors=None,
            returns_status_code=False,
            **kwargs
    ):
        if interface is None:
            raise ValueError('ServerCommand cannot be instanced as separate from a server or interface!')

        if not callable(_callable):
            raise ValueError('ServerCommand class can only be instanced with a callable!')

        self.logger = logging.getLogger('ServerCommand')

        self.interface = interface
        self._callable = _callable
        self.private = private

        # -- "help obj" allows us to redirect the object being described in the help method from the actual callable.
        # -- this is used for decorators, which use transient wrapper methods but actually would want to describe the
        # -- function itself.
        self.help_obj = help_obj or self._callable

        self.arg_defaults = arg_defaults or dict()
        self.arg_types = arg_types or dict()
        self.return_type = return_type

        self.aliases = aliases or list()
        self.former_aliases = former_aliases or list()
        self.returns_status_code = returns_status_code

        self.arg_processors = arg_processors or list()
        self.result_processors = result_processors or list()

        self.accept_encoding = 'text/json'

        # -- this feature allows the user to add extra attributes to their methods, allowing for custom decorators.
        self.extra_attrs = dict()
        if hasattr(self._callable, 'extra_attrs'):
            extra_attrs = getattr(self._callable, 'extra_attrs')

            if not isinstance(extra_attrs, dict):
                raise TypeError(type(extra_attrs))

            for key, value in extra_attrs.items():
                self.extra_attrs[key] = value

    # ------------------------------------------------------------------------------------------------------------------
    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.extra_attrs:
            return self.extra_attrs[item]
        raise AttributeError

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return '%s' % self.help(verbose=False)

    # ------------------------------------------------------------------------------------------------------------------
    def __str__(self):
        # type: () -> str
        return self.__repr__()

    # ------------------------------------------------------------------------------------------------------------------
    def __doc__(self):
        # type: () -> str
        return self.help_obj.__doc__

    # ------------------------------------------------------------------------------------------------------------------
    def help(self, verbose=True):
        # type: (bool) -> str
        """
        Build a helpful string describing this command, using the callable's docstring and the provided type hints
        for this command.

        :return: a helpful type string
        :rtype: str
        """
        result = '[%s] %s (%s) -> %s' % (
            self.__class__.__name__,
            self.help_obj.__name__,
            ', '.join(
                [
                    '%s: %s (%s)' % (key, self.arg_types.get(key), self.arg_defaults.get(key))
                    for key in self.arg_types
                ]
            ),
            str(self.return_type) if self.return_type is not None else 'None'
        )

        if self.aliases:
            result += ' {aliases: %s}' % self.aliases

        if not verbose:
            return result

        result += '\n%s' % self.help_obj.__doc__ if self.help_obj.__doc__ is not None else ''

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        """
        Call this method like a standard callable.
        """
        args, kwargs = self.process_args(args, kwargs)

        _result = self._callable(*args, **kwargs)

        if self.returns_status_code:
            result, code = _result

        else:
            result = _result

        result = self.process_result(result)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def process_args(self, args, kwargs):
        input_args, input_kwargs = args, kwargs

        # -- run all argument processors
        for arg_processor in self.arg_processors:
            processed_args = arg_processor(self, *args, **kwargs)

            # -- every argument processor must return args and kwargs as a tuple of list and dict
            # -- by checking this here, we prevent argument processors that are not functioning correctly
            # -- from corrupting the command process
            if not isinstance(processed_args, tuple):
                raise ClacksBadArgProcessorOutputError(
                    message='Arg processors must return a tuple, got %s!' % type(processed_args),
                    command=self,
                )

            if len(processed_args) != 2:
                raise ClacksBadArgProcessorOutputError(
                    message='Arg processors must return a tuple of length 2, got %s!' % len(processed_args),
                    command=self,
                )

            if not isinstance(processed_args[0], (list, tuple)):
                raise ClacksBadArgProcessorOutputError(
                    message='The first element of the arg processor output must be a list or tuple, got %s!' % (
                        type(processed_args[0])
                    ),
                    command=self,
                )

            if not isinstance(processed_args[1], (dict, collections.OrderedDict)):
                raise ClacksBadArgProcessorOutputError(
                    message='The second element of the arg processor output must be a dictionary, got %s!' % (
                        type(processed_args[1])
                    ),
                    command=self,
                )

            args, kwargs = processed_args

        return args, kwargs

    # ------------------------------------------------------------------------------------------------------------------
    def process_result(self, value):
        # -- run all result processors
        for result_processor in self.result_processors:
            value = result_processor(self, value)
        return value

    # ------------------------------------------------------------------------------------------------------------------
    def digest(self, question):
        # type: (Question) -> Response
        """
        Run this method as a response to a question input.

        This will call the method with the question's input arguments, but also return information about the process,
        like how much time it took to process.
        """
        # -- if the method is private, allow it to be called but not used as a question / answer interface.
        if self.private:
            raise ClacksCommandIsPrivateError(
                message='Cannot access private commands!',
                question=question,
                command=self,
            )

        try:
            args = list(question.args)
        except Exception as e:
            raise ClacksBadCommandArgsError(
                message='Failed to convert positional arguments (%s) to a list!' % question.args,
                command=self,
                question=question,
                tb=e,
            )

        try:
            kwargs = dict(**question.kwargs)
        except Exception as e:
            raise ClacksBadCommandArgsError(
                message='Failed to convert keyword arguments (%s) to a dictionary!' % question.kwargs,
                command=self,
                question=question,
                tb=e,
            )

        args, kwargs = self.process_args(args, kwargs)

        # -- this is not wrapped in a try/except as any unhandled exceptions will be raised as such.
        # -- This way, server commands can choose to implement custom exceptions that clacks can handle
        # -- appropriately.
        _result = self._callable(*args, **kwargs)

        result = _result
        code = ReturnCodes.OK

        if self.returns_status_code and not isinstance(result, (tuple, list)):
            raise ClacksCommandUnexpectedReturnValueError(
                'Command that expected to return a status code did not return an iterable object!'
                ' Got: (%s) but expected a tuple/list!' % type(result),
                question=question,
                command=self,
            )

        # -- if we reach this code, the above statement has not triggered an early out
        if self.returns_status_code:
            result, code = result

        # -- if we get a response object, forward it.
        if isinstance(result, Response):
            result.response = self.process_result(result.response)
            return result

        result = self.process_result(result)

        response = Response(
            header_data=dict(),
            response=result,
            code=code,
        )

        response.accept_encoding = question.accept_encoding

        return response
