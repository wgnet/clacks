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
class ReturnCodes(object):

    NOT_RUN = 0
    OK = 200
    DEPRECATED = 201

    CONNECTION_REJECTED = 400
    NOT_FOUND = 404
    ACCESS_DENIED = 405

    SERVER_ERROR = 500
    BAD_HEADER = 501
    MARSHAL_ERROR = 502
    UNMARSHAL_ERROR = 503

    BAD_QUESTION = 504
    BAD_RESPONSE = 505

    UNHANDLED_EXCEPTION = 600

    INVALID_COMMAND_RETURN_TYPE = 621
    INVALID_COMMAND_ARGUMENTS = 622
