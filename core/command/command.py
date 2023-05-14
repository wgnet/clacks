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
import json
import inspect
import logging

from ..errors import ReturnCodes
from ..package import Question, Response
from ..errors import ClacksBadCommandArgsError


# ----------------------------------------------------------------------------------------------------------------------
class ServerCommand(object):
    """
    Base ServerCommand class. All commands registered to a server must be an instance of this class or a subclass of it.

    It provides basic validation on instance, to ensure the wrapped object is actually callable, and to ensure all
    ServerCommand instances registered are registered as part of a ServerInterface object. This is a basic requirement
    of all Clacks servers, as it ensures a clacks-friendly approach to server construction.

    As we simply wrap the callable, all decorators previously assigned to it are maintained and will function as normal.
    """

    def __init__(
            self,
            interface,
            _callable,
    ):
        from ..interface import ServerInterface

        if not isinstance(interface, ServerInterface):
            raise ValueError('ServerCommand cannot be instanced as separate from an interface!')

        if not callable(_callable):
            raise ValueError('ServerCommand class can only be instanced with a callable!')

        self.logger = logging.getLogger('ServerCommand')

        self.interface = interface
        self._callable = _callable

        # -- cache a function signature
        self._signature = inspect.signature(self._callable)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def signature(self):
        """
        Return a Signature instance, created by the "inspect" module.

        This object is used to create smart properties about the wrapped callable assigned to this ServerCommand, so
        that the command may be interacted with as if it is its callable, without losing the functionalities created by
        Clacks.
        """
        # -- protect this property by not exposing a setter
        # -- this doesn't actually "protect" it - python can't do that. However, this at least lets the developer know
        # -- it's not supposed to be assigned.
        return self._signature

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def return_type(self):
        """
        Gets the type annotation of the function signature of the callable object, if one was given.
        """
        return self.signature.return_annotation

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def is_void(self):
        """
        Returns True if no type annotation for the callable was given for its return type.
        This cannot detect whether nothing is actually returned - just if an annotation was provided!!
        """
        return self.return_type is inspect._empty

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def parameters(self):
        """
        Returns the Signature Parameter objects from the callable's signature.
        """
        return self.signature.parameters

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def arg_defaults(self):
        """
        Based on the callable's annotations, return any default values that may have been given.
        """
        result = dict()
        for key, value in self.signature.parameters.items():
            result[key] = value.default if value.default is not inspect._empty else None
        return result

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def arg_types(self):
        """
        Based on the callable's annotations, return any type annotations that may have been given.
        This can derive types from defaults, if they are provided but type annotations are not.
        """
        result = dict()
        for key, value in self.signature.parameters.items():
            annotation = value.annotation

            if annotation is inspect._empty:
                if key in self.arg_defaults:
                    annotation = type(self.arg_defaults[key])
                else:
                    annotation = None

            result[key] = annotation

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def decorators(self):
        result = list()

        for key in dir(self._callable):
            if key.startswith('_'):
               continue
            result.append(key)

        return result

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def docstring(self):
        """
        Return the docstring of the assigned callable.
        """
        return self._callable.__doc__ or ''

    # ------------------------------------------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        """
        Return this command as a dictionary - this allows us to hash ServerCommand instances to compare them to one
        another.
        """
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
        """
        Return True if this ServerCommand is equal to the other that's given.
        """
        return hash(self) == hash(other)

    # ------------------------------------------------------------------------------------------------------------------
    def __hash__(self):
        """
        Return a hash of this command's to_dict method's result.
        """
        # -- this ensures that server commands decorating the same function are considered equal.
        # -- as server commands must be part of interfaces, python itself is leveraged to prevent collisions, as you
        # -- cannot declare the same method twice within the same class.
        return hash(json.dumps(self.to_dict()))

    # ------------------------------------------------------------------------------------------------------------------
    def get(self, key: str, default: object = None) -> object:
        """
        Get an attribute on this server command's callable object. This functions like a default dict, and ensures that
        ServerCommand instances do not require a standard property layout, opening the door for interfaces to
        implement their own function decorators.
        """
        # -- redirect most getattr calls to the callable
        if key in dir(self._callable):
            return getattr(self._callable, key, default)
        return default

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self) -> str:
        """
        Return a string representation of this ServerCommand with function arguments and return type.
        """
        params = dict()

        for name, param in self.parameters.items():
            annotation = param.annotation
            if not annotation:
                annotation = ''
            else:
                if annotation is inspect._empty:
                    annotation = ''
                else:
                    annotation = f':{annotation}'

            default = param.default
            if not default:
                default = ''
            else:
                if default is inspect._empty:
                    default = ''
                else:
                    default = f' = {default}'

            params[name] = f'{name}{annotation}{default}'

        return_annotation = f' -> {self.return_type}'
        if self.is_void:
            return_annotation = ' -> <void>'

        decorators = ', '.join(self.decorators)

        return f'[{self.__class__.__name__}] ' \
               f'{{{self._callable.__name__}}} ' \
               f'<{decorators}> ' \
               f'({params})' \
               f'{return_annotation}'

    # ------------------------------------------------------------------------------------------------------------------
    def __str__(self) -> str:
        """
        Same as the __repr__ function. (This calls the __repr__ function)
        """
        return self.__repr__()

    # ------------------------------------------------------------------------------------------------------------------
    def __doc__(self) -> str:
        """
        Same as the docstring() property.
        """
        return self._callable.__doc__

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
