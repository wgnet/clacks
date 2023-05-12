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
import json
import logging

from ..errors import ReturnCodes
from ..package import Question, Response
from ..errors import ClacksBadCommandArgsError


# ----------------------------------------------------------------------------------------------------------------------
class ServerCommand(object):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(
            self,
            interface,
            _callable,
    ):
        if interface is None:
            raise ValueError('ServerCommand cannot be instanced as separate from an interface!')

        if not callable(_callable):
            raise ValueError('ServerCommand class can only be instanced with a callable!')

        self.logger = logging.getLogger('ServerCommand')

        self.interface = interface
        self._callable = _callable

    # ------------------------------------------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        result = dict()

        result['interface'] = self.interface.__class__.__name__
        result['_callable'] = self._callable.__name__

        for key in dir(self._callable):
            if key.startswith('_'):
                continue
            result[key] = getattr(self._callable, key)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def __eq__(self, other):
        return hash(self) == hash(other)

    # ------------------------------------------------------------------------------------------------------------------
    def __hash__(self):
        # -- this ensures that server commands decorating the same function are considered equal.
        # -- as server commands must be part of interfaces, python itself is leveraged to prevent collisions, as you
        # -- cannot declare the same method twice within the same class.
        return hash(json.dumps(self.to_dict()))

    # ------------------------------------------------------------------------------------------------------------------
    def get(self, key: str, default: object = None) -> object:
        # -- redirect most getattr calls to the callable
        if key in dir(self._callable):
            return getattr(self._callable, key)
        return default

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self) -> str:
        return '%s' % self.help(verbose=False)

    # ------------------------------------------------------------------------------------------------------------------
    def __str__(self) -> str:
        return self.__repr__()

    # ------------------------------------------------------------------------------------------------------------------
    def __doc__(self) -> str:
        return self._callable.__doc__

    # ------------------------------------------------------------------------------------------------------------------
    def help(self, verbose: bool = True) -> str:
        """
        Build a helpful string describing this command, using the callable's docstring and the provided type hints
        for this command.

        :return: a helpful type string
        :rtype: str
        """
        result = f'[{self.__class__.__name__}] ({self._callable})'

        if not verbose:
            return result

        if self._callable.__doc__:
            result += f'\n{self._callable.__doc__}'

        return result

    # ------------------------------------------------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        """
        Call this method like a standard callable.
        """
        return self._callable(*args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def digest(self, question: Question) -> Response:
        """
        Run this method as a response to a question input.

        This will call the method with the question's input arguments, but also return information about the process,
        like how much time it took to process.
        """
        try:
            args = list(question.args)

        except Exception as e:
            raise ClacksBadCommandArgsError(
                message=f'Failed to convert positional arguments ({question.args}) to a list!',
                command=self,
                question=question,
                tb=e,
            )

        try:
            kwargs = dict(**question.kwargs)

        except Exception as e:
            raise ClacksBadCommandArgsError(
                message=f'Failed to convert keyword arguments ({question.kwargs}) to a dictionary!',
                command=self,
                question=question,
                tb=e,
            )

        # -- this is not wrapped in a try/except as any unhandled exceptions will be raised as such.
        # -- This way, server commands can choose to implement custom exceptions that clacks can handle
        # -- appropriately.
        _result = self._callable(*args, **kwargs)

        result = _result
        code = ReturnCodes.OK

        # -- if we get a response object, forward it.
        if isinstance(result, Response):
            return result

        response = Response(
            header_data=dict(),
            response=result,
            code=code,
        )

        response.accept_encoding = question.accept_encoding

        return response
