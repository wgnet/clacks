```pip install git+https://github.com/MaVCArt/clacks.git@main```

# clacks

---

A NOTE ON SECURITY

**Clacks was written for the express purpose of creating a convenient network of servers and clients within a protected,
firewalled environment, where every user is trusted and malicious attackers are not expected.**

**It was _not_ written with security concerns in mind, and as such it is strongly discouraged to use this framework on
any public-facing interfaces.**

**If you still wish to implement features like authentication or user identification, please refer to the topic of
`Adapters`, as that is the feature designed to attach additional behaviour to header data.**

---

```
GNU Terry Pratchett
```

```
Zen of clacks

A Server can have any number of Handlers
Handlers handle incoming traffic
Servers handle tasks in the order they arrived
Adapters can interject and modify server behaviour
Handlers understand headers and are paired with Marshallers
Marshallers turn packages into requests or results into packages
Interfaces are how we actually implement commands
Interface decorators expand behaviour
```

`clacks` (its name inspired by the fictional "clacks" system of Terry Pratchett's Discworld novels),
sets out to accomplish one simple goal: make it as easy as possible for developers, specifically
tools programmers and TAs, to make their applications communicate with one another, and to tie major DCCs like Maya,
3ds Max, Houdini, and Substance together into one single network.

`clacks` takes a somewhat different approach to server architecture, namely one that discards the notion of
network transaction security entirely, in favor of interoperability and accessibility. As such, this framework was 
designed to be run behind a strong firewall, on a protected private network.

Typical scenarios that would fall in the "safe" category would be a setup where a server is set up on one machine,
and it expects incoming connections only from other machines on that same, firewalled, internal network. A real-world
use case for this might involve (in a game development studio) setting up a slave machine to perform heavy operations,
such as with Houdini or Maya, and to have that machine operate as a way for a developer to set up a service-like API
easily, without needing to find a way to deploy complex processing software to multiple users.

Following on from this, clacks sets out to achieve a few goals;

```
Clacks Servers can be taught to speak any transfer Protocol
A developer should never have to sub-class the provided Server Classes

A typical Server should be formed of:
- A Server
- An Interface
- A Handler
- A Marshaller

Adapters are optional, and provide the ability to inject or filter data. This enables the creation of
user authentication services, should such techniques be required.
```

---

#### ``clacks`` can be taught to speak everything

As laid out in the `zen of clacks`, `clacks` is set up in a modular way. Core `servers` are little more than managers for
`Handlers`, which in turn contain `Marshallers`. The `Handlers` receive I/O through the `Marshallers`, and the `server`
is then asked to perform a task. This task, implemented through `Interfaces`, is then executed, and its result is returned
to the `Handler`, which tells its `Marshaller` to serialize the result into a response package, before responding to the
client that connected to it originally.

This modular approach means that, given that a server can have any number of `Handlers` registered to it, a developer can
simply implement a Handler to parse, say, an HTTP request, and suddenly the server can process web requests! In fact, 
given that `Marshallers` and `Handlers` are different things, this is the _only_ thing a developer has to do to teach
`clacks` to speak a new transfer protocol.

---

#### Creating a server

```python
import clacks

# -- create a server. This does not open any ports.
server = clacks.ServerBase(identifier='MyServer')

# -- create a handler and register it. Just registering it will _still_ not open the port.
handler = clacks.handler.JSONHandler(clacks.marshaller.JSONMarshaller())
server.register_handler('localhost', 5555, handler)

# -- at this point, no ports have been opened and nothing is actively listening.

# -- now we start the server, which will, for each handler, open a port and start listening.
# -- if we pass blocking=True, that will block the thread this is called in (usually the main one)
# -- if we pass blocking=False, the current thread will continue.
server.start(blocking=True)
```

#### Connecting to a server

```python
import clacks

# -- create a proxy - instancing it will establish a connection instantly.
# -- Note that unlike with servers, server _proxies_ require a separate class instance per port.
json_proxy = clacks.ClientProxyBase(
  ('localhost', 5555), 
  clacks.handler.JSONHandler(clacks.marshaller.JSONMarshaller())
)

# -- in RPYC style, once acquired, a proxy class can be called as if operating on the server instance it represents.
# -- any attribute "get" methods are automatically turned into server commands, unless otherwise implemented in the
# -- proxy subclass in question.
json_proxy.list_commands()
```

---
A consequence of this simple set of rules is that clacks servers can technically listen to any number of ports
on any number of hosts they are allowed to open sockets on.

This might seem strange, but it creates a powerful architecture, where applications or platforms that are restricted
to a particular type of server, or data, can interact safely with any clacks server instance that has the right
handler/marshaller combination listening to it.

A summary of the `clacks` server architecture;

- `Server` (identifier, task queue) Servers handle the actual Task Queue
  - `Adapter` Adapters implement a large contingent of methods to modify server behaviour (more below) 
  - `Handler` (host, port, marshaller) Handlers handle traffic and connections
    - `Marshaller` Marshallers perform serialization.
  - `Interface` Interfaces, registered on servers, provide a way to quickly extend functionality 

### Servers, Handlers and Marshallers

---

#### High Level

```
Handlers listen and speak to sockets, and understand a transfer protocol.
This means that handlers take care of headers and raw byte I/O, including pre-declaring package size.

Marshallers know how to read and write the data that handlers send.
This means they know how to turn raw data into Questions and Answers.

Servers know what to do with Questions, and respond with Answers.
This means servers supply the actual behaviour that Questions trigger.

All functional behaviour is implemented using Interfaces.

Adapters can be used to modify server behaviour and implement features like
additional header data, user authentication and resource access.
```

---

#### Servers

`Servers`, in `clacks`, are effectively Task Queues, and receive incoming command requests from their handlers.
The `Server` instance is responsible for executing each command (referred to as `Questions` within the `clacks`
framework), and returning the result, or the traceback information, if an error occurred.

`Servers` do **NOT** themselves listen to any sockets. That is the `Handler`'s job.

```
Servers implement commands that trigger the behaviour triggered by Questions.
Servers are expected to respond with Answers for the Handlers to send back.
```

Implementing a server can be done without needing to override a single internal method. In most cases, overriding server methods should not be necessary; creating functionaly is all done using `interfaces`, so unless you wish to change or override a very low-level behaviour of how the server works, (like how it executes commands), you should not need to override any internal methods.

```python
import clacks

# -- instance the server. This does not start it!
server = clacks.ServerBase('My Own Server', start_queue=False)

# -- register a handler for the server.
# -- This example uses the built-in "simple" handler with the built-in "simple" marshaller.
host, port = server.register_handler_by_key('localhost', 'simple', 'simple')

# -- start the server, non-blocking, which means the code continues to run below.
# -- this will start the server's command queue on a thread.
server.start(blocking=False)
```

---

#### Interfaces

`Interfaces` are the convenience path that `clacks` provides for developers to quickly scale the functionality available to a given server, while allowing for easy re-use of that functionality, as well.

`Interfaces` are relatively simple, mostly self-contained (though this is not a defining property) collections of functions that a server can make use of. Some of these are exposed as publicly-accessible `ServerCommands`, while others, decorated with the `@clacks.private` decorator, can only be used by the server and its interfaces, while being inaccessible to clients.

When an `interface` is registered, the server will iterate over all the keys in its `__dict__` attribute, and register any values it finds that are callable as functions, as `ServerCommands`. This includes commands decorated with the `private` decorator, which are still registered as fully valid `ServerCommand` instances for use by the server itself and any sibling interfaces.

`Interfaces` are expected to internalize their functionality as much as is feasible, though interface-inter-dependencies are possible. The developer is expected to manage these, as the framework does not (as yet) implement any functionality to expose a list of dependent interfaces when registering an interface.

---

### Server Commands

The `ServerCommand` class is where `clacks`' functionality is implemented. While `interfaces` might provide them in the first place, `ServerCommand`s are how the server knows what to do with them. For each `interface` a `server` registers, it fetches all that interface's callable methods, and registers them to the server as a `ServerCommand` instance, along with any annotations the developer may have provided in the form of `command decorators`.

These annotations are optional; a developer can implement a perfectly functional interface without ever decorating a single method. However, due to the additional information these decorators can provide, a developer can leverage them to provide otherwise tricky-to-implement behaviour. The most common and obvious use case for this behaviour is type checking and enforcement; using `ServerCommand` decorations, we can easily implement an argument processor / return value processor that raises an exception if the incoming or outgoing data does not follow a particular rule, like it needing to be of a very specific variable type.

A typical server command may be implemented as follows:

```python
import clacks

@clacks.takes({'value': str, 'other_value': bool})
@clacks.returns(bool)
def server_command_example(value, other_value):
	if value != 'expected value':
		return False
	if other_value != 'other expected value':
		return False
	return True
```

And registered like so:

```python
server.register_command('server_command_example', server_command_example)
```

However, note that since we provide an arbitrary string as the lookup key for the server command, one can theoretically
register a command under a different key:

```python
server.register_command('this_works_too', server_command_example)
```

**note**, that every mechanism that makes use of lookup keys in `clacks` enforces a string object-name-compatible 
validation check. This means that only alphanumeric characters (no whitespaces) are allowed to be used for server 
command keys.

This is done to ensure that servers can acquire command instances using their __getattr__ method, allowing commands
to be retrieved using the regular "object.property" mechanism, which is designed for use by sibling server interfaces.

##### Command Decorators

`clacks` ships with a set of command decorators we can use to decorate `server commands`, that tell the server something
about them. In and of themselves, these decorators provide little more than convenience, but they do open the 
door to nice, but otherwise difficult features, such as argument type enforcement.

Additionally, `ServerCommands` make use of these decorators to construct the output of their `help()` method, 
which a developer can call to find out more about the method. This provides a nice utility to create accessible APIs, 
especially when using clacks in the context of REST APIs.

The available standard decorators are as follows:

```aka```

the **aka**, or "also known as" decorator tells the server that this command should be exposed under more than one name.
This allows the developer to expose the same methods under different names, to make it easier to implement features
for APIs and protocols that enforce their own rules for method names 
(like the HTTP protocol, where all command names are upper case, like POST, GET, PUT etc...)

```fka```

**fka**, or "formerly known as" is the previous decorator's antithesis; methods decorated with this decorator
can tell the server to register the given aliases as fully functional commands, but any commands called 
under those names will receive a logging warning that the invoked command is due to be deprecated. 
This makes it slightly easier to implement servers with pending API changes.

```takes```

**takes** is simply a type hinting mechanism. It lets the ServerCommand know which type of argument to expect for each
named argument provided. This can be achieved using standard Python3 type hinting as well, but for older implementations
this is a nice convenience method.

```returns```

Another type hinting method; this one just declares the type of the returned value(s) for the server command.

```private```

**private** commands are not accessible on the server as publicly callable commands. However, they may be called
by sibling interfaces parented to the same server. This allows for the creation of methods that can provide utility
to the interface developer without needing to worry about its visibility.

It is worth mentioning that private methods are _visible_ to the user. They are registered as full ServerCommand 
instances, but calling them remotely results in an error.

```hidden```

**hidden** commands go one step further than **private** ones. Hidden commands are only visible to the interface that
declares them, and are not registered as ServerCommands, and therefore not easily accessible on the server.

#### Argument and Result Processors

The `process_arguments` and `process_result` decorators deserve their own section. They provide what effectively amounts
to pre-and-post-processing of function input and output. This can be quite powerful, as it enables the user to build
things like filtering and validation mechanisms.

Argument and result processors, can, for example, provide type hint enforcement, result type enforcement, argument
pre-processing (such as taking incoming JSON data and converting it to keyword arguments), and other types of 
translation that make mass data handling a little easier.

```process_arguments```

This decorator takes one argument; a list of callables. Each of these callables takes three arguments;
the server command, the positional arguments (a list) and the keyword arguments (a dictionary) that were passed to the
function when it was called.

This allows a developer to interject into argument processing and change the arguments as they pass through.
The expected result of the callable is a tuple of (list, dict) with the positional and keyword arguments as they should
be passed on to the next processor, or to the server command itself.

A typical argument processor looks a bit like this;

```python
def example_arg_processor(server_command, *args, **kwargs):
    # -- do something to the arguments
    return args, kwargs
```

```process_result```

Like argument processors, the result processor works the same, but more simply; it simply takes the server command and 
its returned result, and is able to change that result in some way by returning its own.

A typical result processor looks like this;

```python
def example_result_processor(server_command, result):
    # -- do something to the result 
    return result
```

---

#### Handlers

Each `Handler` is responsible for implementing the behaviour that decides how to listen to the socket, how to connect to
it, how it receives the package header (if there is one at all), and how it receives the package data. Importantly,
the `Handler` does **NOT** implement serialization/de-serialization methods for the packages _contents_, as this is a 
`Marshaller` job.

The most common behaviour for a `Handler` is to receive a header, which then indicates the size of the rest of the
package. In most common server types, this is implemented by receiving the header one byte at a time, until a known
delimiter is encountered, which indicates that the header is complete.

```
For HTTP servers, for example, this delimiter is the sequence "\r\n\r\n".
```

In some cases, rather than looking for a delimiter, the `handler` might know how big the header will be, based on the
implemented protocol. the `rpyc` Handler is one such `handler`.

`Handlers` are the bread and butter of `clacks`. They are the reason clacks servers can talk to 
different interfaces, using different protocols, and different formats. `Handlers` are where the protocols, like
HTML, RPyC, XML, JSON, and others that govern the logistics of data transfer are actually implemented.

A typical handler implements only one important mechanism, formed of two keys components:

- It pre-declares to the receiving handler some metadata (like the number of bytes) about the content it is about to 
  send. This allows the receiver to modify its behaviour based on the expected incoming data.

- It implements the key components of the major data transfer protocols, like HTTP or XMLRPC. 
  This is usually done in the form of some kind of recognized data structure in the header buffer, followed 
  by a delimiter.

In some cases, no delimiter is used; instead, a header is expected to have a certain fixed size, say, 64 bytes for 
example. The sending handler is expected to pad any empty space, while the receiver will blindly receive that 
many bytes. In most cases, the header is the primary method by which we teach `clacks` to "speak" different protocols.

```
Note: there are currently no available clacks mechanisms to detect a handler type from a port.
If you try to make a proxy talk to a server using different handlers, you will simply get a low-level handler
or marshaller error.

The same notice is valid for proxy/server combinations with mismatching marshallers, even if their handlers match.
```

---

#### Marshallers

`Marshallers` implement how data is serialized and de-serialized. Their serialization method is expected to return
a byte sequence, and their de-serialization method is expected to return a dictionary.

This last part is crucial; it is this global standardization of how the data makes it into the server that makes it so
clacks servers can behave as multiple server types as once; by the time the package gets to the Task Queue,
the data has been standardized into a bog-standard Dictionary, which acts as a keyword argument container for the method
the user wants to call.

`Marshallers` are the bread and butter of how data makes it from a proxy to a server and vice versa: 
they turn Package instances into Bytes, and Back.

```
Note: Adapters can implement post- and pre-buffer-compile steps that could be used to implement content encryption, 
while leaving header data unencrypted. Additionally, this step could be used to supply compression, which could reduce 
the strain on socket traffic at the expense of computation on the server.
```

```
While it is possible to send content of any size, it is strongly discouraged to use marshallers to transfer 
large files from a proxy to a server. The marshaller could be prone to data corruption, depending on its implementation,
 and it would create a large computational overhead to compile and send a buffer that large.

Instead, clacks is shipped with a "file_io" interface that implements proxy/client streaming sockets which use 
streaming to avoid hogging memory on the server machine, and which does not risk data corruption, as the data
is transfered as raw bytes, unencoded.
```

```
Note: the developer is expected to know which marshaller type to use when connecting a proxy to a server. 
There are currently no mechanisms to allow clacks to detect the handler/marshaller setup of a particular port.
```

---

#### Interfaces

`Interfaces` are the nice Python sugar that `clacks` takes advantage of, by creating a base `ServerInterface` class
that may be inherited by a user as an easy-to-use yet infinitely customizable way to expose commands to an end user.
`Interfaces` are the magic that makes `clacks` tick, and they are behind the extensibility of its servers' APIs.

At their core, `clacks` servers are pretty naked objects; they do not implement any functionality beyond the mechanisms
necessary to function as a minimally functional server, with mechanisms to register `handlers` and `interfaces`.

This is where `interfaces` come in - they employ the concept of `class composition` to create behaviour that any server
can make use of, through its overridden behaviour in the `__getattr__` method of the `ServerBase` class.

A typical interface might look like this:

```python
import clacks

# ----------------------------------------------------------------------------------------------------------------------
class MyServerInterface(clacks.ServerInterface):
    
    # ------------------------------------------------------------------------------------------------------------------
	@clacks.private
	def my_private_method(self, value):
		print(value)
    
    # ------------------------------------------------------------------------------------------------------------------
	@clacks.takes(dict(value=str))
	@clacks.returns(bool)
	def my_standard_command(self, value):
		if value == "":
			return False
		return True
    
    # ------------------------------------------------------------------------------------------------------------------
	def my_naked_method(self):
		return 'This method will still work'

    # ------------------------------------------------------------------------------------------------------------------
	@clacks.aka(['other'])
	def my_aliased_method(self):
		return 'You can also call this method as "server.other"'
```

---

#### Adapters

`Adapters` are how we allow developers to attach additional behaviour to the internal mechanisms for `servers`,
`handlers` and `marshallers`, exposing for each `Adapter` instance a large number of methods that can be overridden.

A typical example of an adapter is the profiling adapter: it utilizes the `pre-digest` and `post_digest` methods to 
create full profile dumps of individual server commands, and the `post_add_to_queue` and `post_respond` to measure
the total time between the arrival of a command and the server's response to it.

Another example, which does not come pre-packaged with `Clacks`, could be user identification; `adapters` can be used
to inject header data into a command, and since they work for `proxy` and well as `server` objects, a sender/receiver
structure could be created where the proxy adapter inserts information about the client, and the server adapter decides
what to do with it.

Should the server adapter decide that the given information is not correct, it can then raise an exception to abort the
process early and have the server respond with an exception, without ever invoking the requested command.
