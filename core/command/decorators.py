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
# ----------------------------------------------------------------------------------------------------------------------
def aka(aliases=None):
    """
    AKA - Also Known As

    This decorator tells the server to register the decorated callable under more than one key. This allows the
    developer to expose a given command under different monikers.
    """
    def wrapper(fn):
        fn.aliases = aliases
        fn.is_server_command = True
        return fn
    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
def fka(former_aliases=None):
    """
    FKA - Formerly Known As

    This decorator tells the server that a given set of command aliases is deprecated. This will not prevent the
    command from being called, but it will log a warning, informing the caller that the function is due to be
    deprecated and should no longer be called.
    """
    def wrapper(fn):
        fn.former_aliases = former_aliases
        fn.is_server_command = True
        return fn
    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
def private(fn):
    """
    Tells the server this method is private. This ensures that it cannot be called by a client, but it may be called
    by the server itself. Private methods are not hidden - they still get registered as functions!
    """
    fn.private = True
    fn.is_server_command = True
    return fn


# ----------------------------------------------------------------------------------------------------------------------
def hidden(fn):
    """
    Tells the server this method is hidden. This ensures the decorated method is never registered as a server command.
    This is used in interfaces, which are expected to explicitly declare internal methods using
    this decorator to ensure that they do not get registered as server commands.
    """
    fn.hidden = True
    fn.is_server_command = False
    return fn
