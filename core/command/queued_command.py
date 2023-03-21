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
import socket
import time
import uuid

from .command import ServerCommand
from ..package import Question, Response


# ----------------------------------------------------------------------------------------------------------------------
class QueuedServerCommand(ServerCommand):
    """
    Queued Command class, forces transactions to go through the queue when digested directly.
    """

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
    ):
        super(QueuedServerCommand, self).__init__(
            interface,
            _callable,
            private=private,
            arg_defaults=arg_defaults,
            arg_types=arg_types,
            return_type=return_type,
            help_obj=help_obj,
            aliases=aliases,
            former_aliases=former_aliases,
            arg_processors=arg_processors,
            result_processors=result_processors,
            returns_status_code=returns_status_code,
        )

        self.responses = dict()

    @classmethod
    def from_command(cls, command):
        # type: (ServerCommand) -> QueuedServerCommand
        return QueuedServerCommand(
            command.interface,
            command._callable,
            private=command.private,
            arg_defaults=command.arg_defaults,
            arg_types=command.arg_types,
            return_type=command.return_type,
            help_obj=command.help_obj,
            aliases=command.aliases,
            former_aliases=command.former_aliases,
            arg_processors=command.arg_processors,
            result_processors=command.result_processors,
            returns_status_code=command.returns_status_code
        )

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        # type: () -> str
        return '[Queued Command] %s' % self.help(verbose=False)

    # ------------------------------------------------------------------------------------------------------------------
    def respond(self, connection, transaction_id, response):
        # type: (socket.socket, str, Response) -> None
        self.responses[transaction_id] = response

    # ------------------------------------------------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        question = Question(dict(), self.aliases[0], *args, **kwargs)
        return self.queue(question)

    # ------------------------------------------------------------------------------------------------------------------
    def queue(self, question):
        # type: (Question) -> Response
        # -- generate a new UUID
        transaction_id = str(uuid.uuid4())

        # -- add instructions to the server queue, and wait until the queue has processed it.
        self.interface.add_to_queue(self, None, transaction_id, question.header_data, question.payload)

        self.responses[transaction_id] = None

        # -- poll to see if our response has been received
        while self.responses[transaction_id] is None:
            time.sleep(0.01)

        response = self.responses[transaction_id]
        del self.responses[transaction_id]

        return response
