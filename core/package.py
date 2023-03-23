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

Packages
========

There are only two package types:

Questions: contain a command and expect an answer
Answers: respond to a question, contain information about the digest of the question answered.

With the Question/Answer model, Clacks implements all server behaviours.
There should be no reason to create new subclasses for package types.

"""
from .errors import error_from_key, key_from_error_type


# ----------------------------------------------------------------------------------------------------------------------
class Package(object):
    """
    Base class for all packages, both Questions and Answers.
    This works with a payload attribute, which contains all arbitrary data that Questions and Answers can contain.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, payload):
        # type: (dict) -> None
        self.payload = payload
        self.accept_encoding = 'text/json'

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def load(cls, header_data, data):
        # type: (dict, dict) -> Package
        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def header_data(self):
        # type: () -> dict
        return self.payload.get('header_data')

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def keep_alive(self):
        # type: () -> bool
        if 'Connection' not in self.header_data:
            return False
        return self.header_data.get('Connection') == 'keep-alive'


# ----------------------------------------------------------------------------------------------------------------------
class Question(Package):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, header_data, command, *args, **kwargs):
        # type: (dict, str, list, dict) -> None
        super(Question, self).__init__(
            payload=dict(
                header_data=header_data,
                command=command,
                args=args,
                kwargs=kwargs
            )
        )

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return 'Question %s %s %s' % (self.command, self.args, self.kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def load(cls, header_data, data):
        # type: (dict, dict) -> Question
        if 'header_data' in data.get('kwargs', dict()):
            header_data.update(data['kwargs']['header_data'])
            del data['kwargs']['header_data']

        if 'command' in data.get('kwargs', dict()):
            data['command'] = data['kwargs']['command']
            del data['kwargs']['command']

        return Question(
            header_data,
            data['command'],
            *data.get('args', list()),
            **data.get('kwargs', dict())
        )

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def args(self):
        # type: () -> list
        return self.payload.get('args', list())

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def kwargs(self):
        # type: () -> dict
        return self.payload.get('kwargs', dict())

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def command(self):
        # type: () -> str
        return self.payload.get('command')


# ----------------------------------------------------------------------------------------------------------------------
class Response(Package):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(
            self,
            header_data=None,
            response=None,
            code=0,
            tb=None,
            warnings=None,
            errors=None,
            info=None,
            **kwargs
    ):
        # type: (dict, object, int, (Exception, str), list, list, dict, dict) -> None
        super(Response, self).__init__(
            payload=dict(
                header_data=header_data,
                response=response,
                code=code,
                tb=tb,
                warnings=warnings,
                errors=errors,
                info=info,
                **kwargs
            )
        )

        # -- refresh traceback on initialize.
        self.traceback = self.traceback

        # -- initialize errors
        self.errors = errors
        self.warnings = warnings

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return 'Response %s' % self.payload

    # ------------------------------------------------------------------------------------------------------------------
    @classmethod
    def load(cls, header_data, data):
        # type: (dict, dict) -> Response
        if 'header_data' in data:
            header_data.update(data['header_data'])
            del data['header_data']

        return Response(
            header_data,
            **data
        )

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def response(self):
        # type: () -> str
        return self.payload.get('response')

    # ------------------------------------------------------------------------------------------------------------------
    @response.setter
    def response(self, value):
        self.payload['response'] = value

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def code(self):
        # type: () -> int
        return int(self.payload.get('code', '200'))

    # ------------------------------------------------------------------------------------------------------------------
    @code.setter
    def code(self, value):
        self.payload['code'] = str(int(value))

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def traceback(self):
        # type () -> str
        value = self.payload.get('tb')

        if value is None:
            return None

        try:
            b = bytearray.fromhex(value)
            result = b.decode('unicode_escape')
            return result
        except:
            return value

    # ------------------------------------------------------------------------------------------------------------------
    @traceback.setter
    def traceback(self, value):
        if value is None:
            return

        tb_type = self.traceback_type or Exception

        if not isinstance(value, Exception):
            value = tb_type(value)

        try:
            key = key_from_error_type(type(value))
        except ValueError:
            key = 'exception'

        self.traceback_type = key

        self.payload['tb'] = repr(value).encode('utf-8').hex()

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def traceback_type(self):
        # type() -> str
        tb_type = self.payload.get('tb_type')
        if not tb_type:
            return None
        return error_from_key(tb_type)

    # ------------------------------------------------------------------------------------------------------------------
    @traceback_type.setter
    def traceback_type(self, value):
        if error_from_key(value) is None:
            raise ValueError('Error type %s is not a registered error type!' % value)
        self.payload['tb_type'] = value

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def warnings(self):
        if 'warnings' not in self.payload:
            self.payload['warnings'] = list()
        if self.payload.get('warnings') is None:
            self.payload['warnings'] = list()
        return self.payload.get('warnings')

    # ------------------------------------------------------------------------------------------------------------------
    @warnings.setter
    def warnings(self, value):
        if value is None:
            # -- if the value is None, initialize an empty list.
            self.payload['warnings'] = list()
        else:
            # -- type conversion out of safety
            self.payload['warnings'] = list(value)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def errors(self):
        if 'errors' not in self.payload:
            self.payload['errors'] = list()
        if self.payload.get('errors') is None:
            self.payload['errors'] = list()
        return self.payload.get('errors', list())

    # ------------------------------------------------------------------------------------------------------------------
    @errors.setter
    def errors(self, value):
        if value is None:
            # -- if the value is None, initialize an empty list.
            self.payload['errors'] = list()
        else:
            # -- type conversion out of safety
            self.payload['errors'] = list(value)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def info(self):
        return self.payload.get('info')

    # ------------------------------------------------------------------------------------------------------------------
    @info.setter
    def info(self, value):
        self.payload['info'] = value

    # ------------------------------------------------------------------------------------------------------------------
    def raise_for_status(self):
        typ = Exception
        if self.traceback_type is not None:
            typ = self.traceback_type

        raise typ(self.traceback)
