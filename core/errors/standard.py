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
from .codes import ReturnCodes
from . import register_error_type


# ----------------------------------------------------------------------------------------------------------------------
class ClacksExceptionBase(Exception):
    key = 'clacks_exception'
    label = 'Exception'
    code = ReturnCodes.UNHANDLED_EXCEPTION

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, message, **kwargs):
        Exception.__init__(self, message)
        self.kwargs = kwargs

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def message(self):
        return repr(self)

    # ------------------------------------------------------------------------------------------------------------------
    def __str__(self):
        return '[Clacks][%s] %s' % (self.label, self.message)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksCommandErrorBaseBase(ClacksExceptionBase):
    key = 'clacks_command_error'
    label = 'Command Error'
    code = None

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, message, question=None, command=None, response=None, tb=None, **kwargs):
        ClacksExceptionBase.__init__(self, message, **kwargs)
        self.question = question
        self.command = command
        self.response = response
        self.traceback = str(tb)

    # ------------------------------------------------------------------------------------------------------------------
    def __str__(self):
        return '[Clacks][%s] %s\n\tQuestion: %s\n\tCommand: %s\n\tResponse: %s\n\tTraceback: %s' % (
            self.label,
            self.message,
            self.question,
            self.command,
            self.response,
            self.traceback,
        )


# ----------------------------------------------------------------------------------------------------------------------
class ClacksUnrecognizedCommandAliasError(ClacksCommandErrorBaseBase):
    key = 'clacks_unrecognized_command_alias'
    label = 'Unrecognized Command Alias'
    code = ReturnCodes.NOT_FOUND


register_error_type(ClacksUnrecognizedCommandAliasError.key, ClacksUnrecognizedCommandAliasError)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksBadCommandArgsError(ClacksCommandErrorBaseBase):
    key = 'clacks_bad_command_args'
    label = 'Bad Command Args'
    code = ReturnCodes.BAD_QUESTION


register_error_type(ClacksBadCommandArgsError.key, ClacksBadCommandArgsError)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksCommandUnexpectedReturnValueError(ClacksCommandErrorBaseBase):
    key = 'clacks_command_unexpected_return_type_error'
    label = 'Unexpected Command Return Type'
    code = ReturnCodes.INVALID_COMMAND_RETURN_TYPE


register_error_type(ClacksCommandUnexpectedReturnValueError.key, ClacksCommandUnexpectedReturnValueError)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksCommandIsPrivateError(ClacksCommandErrorBaseBase):
    key = 'clacks_command_is_private_error'
    label = 'Command is Private'
    code = ReturnCodes.ACCESS_DENIED


register_error_type(ClacksCommandIsPrivateError.key, ClacksCommandIsPrivateError)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksClientConnectionFailedError(ClacksCommandErrorBaseBase):
    key = 'clacks_client_connection_failed_error'
    label = 'Client Connection Failed'
    code = ReturnCodes.CONNECTION_REJECTED


register_error_type(ClacksClientConnectionFailedError.key, ClacksClientConnectionFailedError)


# ----------------------------------------------------------------------------------------------------------------------
class ClacksCommandNotFoundError(ClacksCommandErrorBaseBase):
    key = 'clacks_command_not_found_error'
    label = 'Command Not Found!'
    code = ReturnCodes.NOT_FOUND


register_error_type(ClacksCommandNotFoundError.key, ClacksCommandNotFoundError)
