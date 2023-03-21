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
import logging


# ----------------------------------------------------------------------------------------------------------------------
class ServerCommandDigestLoggingHandler(logging.Handler):

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        logging.Handler.__init__(self, level=logging.WARNING)
        self.warnings = list()
        self.errors = list()

        self.started = False

    # ------------------------------------------------------------------------------------------------------------------
    def flush(self):
        self.warnings = list()
        self.errors = list()

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.started = True

    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        self.started = False
        self.flush()

    # ------------------------------------------------------------------------------------------------------------------
    def emit(self, record):
        if not self.started:
            return

        if record.levelno == logging.WARNING:
            self.warnings.append(record.msg)

        if record.levelno in [logging.ERROR, logging.CRITICAL, logging.FATAL]:
            self.errors.append(record.msg)
