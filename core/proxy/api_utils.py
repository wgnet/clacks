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
import inspect


POSITIONALS = ['args']
KEYWORDS = ['kwargs', 'keywords', 'kwds']


# ----------------------------------------------------------------------------------------------------------------------
def get_api_parts(module):
    # -- break down a module into functions, classes, submodules and variables
    functions, classes, modules, variables = list(), list(), list(), list()

    for prop in dir(module):
        value = getattr(module, prop)

        if inspect.ismodule(value):
            modules.append(value)
            continue

        if inspect.isclass(value):
            classes.append(value)
            continue

        if inspect.isfunction(value):
            functions.append(value)
            continue

        if inspect.isbuiltin(value):
            functions.append(value)
            continue

        if isinstance(value, object):
            variables.append(prop)
            continue

    return functions, classes, modules, variables


# ----------------------------------------------------------------------------------------------------------------------
def indent(lines):
    old_lines = lines.splitlines()
    new_lines = list()
    for line in old_lines:
        new_lines.append('\t%s' % line)
    return '\n'.join(new_lines)


# ----------------------------------------------------------------------------------------------------------------------
def format_args(args):
    formatted_args = list()

    for arg in args:
        for pos in POSITIONALS:
            if arg == pos:
                arg = '*%s' % pos

        for kw in KEYWORDS:
            if arg == kw:
                arg = '**%s' % kw

        formatted_args.append(arg)

    return formatted_args


# ----------------------------------------------------------------------------------------------------------------------
def clean_docstring(docstring):
    if not docstring:
        return ''

    doc_lines = docstring.splitlines()
    new_doc_lines = list()

    for line in doc_lines:
        line = line.lstrip().rstrip()
        line = line.strip('\t').strip('\n').lstrip('\t').lstrip('\n').lstrip().strip()
        new_doc_lines.append('%s' % line)

    docstring = '\n'.join(new_doc_lines)
    docstring = docstring.replace('\r', '\n')

    while '\n\n' in docstring:
        docstring = docstring.replace('\n\n', '\n')

    docstring = indent(docstring)

    return docstring


# ----------------------------------------------------------------------------------------------------------------------
def get_args_from_callable(callable_obj):
    return callable_obj.__code__.co_varnames


# ----------------------------------------------------------------------------------------------------------------------
def generate_function_api(function, parent_obj):
    if not hasattr(function, '__code__'):
        return ''

    template = """def {function_name}(self{args}):\n\t{docstring}{invocation}\n"""
    args = get_args_from_callable(function)

    formatted_args = format_args(args)

    if len(formatted_args) > 2:
        if formatted_args[0] == '*args' and formatted_args[1] == '**kwargs':
            formatted_args = formatted_args[:1]

    fn_name = function.__code__.co_name

    if not fn_name:
        return ''

    arg_string = ', '.join(formatted_args)

    doc_lines = clean_docstring(function.__doc__)

    invocation = 'return %s.%s(%s)' % (parent_obj, fn_name, arg_string)

    return template.format(
        function_name=fn_name,
        args=', %s' % arg_string if arg_string else '',
        docstring='\"\"\"\n\t[GENERATED API FUNCTION]\n%s\n\t\"\"\"\n\t' % doc_lines,
        invocation=invocation
    )


# ----------------------------------------------------------------------------------------------------------------------
def generate_class_api(parent_name, cls_object):
    obj_name = cls_object.__name__

    if not obj_name:
        return ''

    function = cls_object.__init__

    if not hasattr(function, '__code__'):
        return ''

    template = """def {function_name}({args}):\n\t{docstring}{invocation}\n"""
    args = get_args_from_callable(function)

    formatted_args = format_args(args)

    if len(formatted_args) > 3:
        if formatted_args[1] == '*args' and formatted_args[2] == '**kwargs':
            formatted_args = formatted_args[:1]

    arg_string = ', '.join(formatted_args)

    doc_lines = clean_docstring(function.__doc__)

    invocation = 'return %s.%s(%s)' % (parent_name, obj_name, ', '.join(formatted_args[1:]))

    init_str = template.format(
        function_name=obj_name,
        args=arg_string,
        docstring='\"\"\"\n\t[GENERATED API CLASS]\n%s\n\t\"\"\"\n\t' % doc_lines,
        invocation=invocation
    )

    return init_str


# ----------------------------------------------------------------------------------------------------------------------
def generate_module_api(parent_name, parent_module_name, module_object):
    template = """@property\ndef {function_name}(self):\n\t{docstring}{invocation}\n"""

    module_name = module_object.__name__
    if parent_module_name in module_name:
        module_name = module_name.replace('%s.' % parent_module_name, '')

    formatted_obj_name = module_name.replace('.', '_')

    doc_lines = clean_docstring(module_object.__doc__)

    invocation = 'return %s.%s' % (parent_name, module_object.__name__)

    return template.format(
        function_name=formatted_obj_name,
        docstring='\"\"\"\n\t[GENERATED API MODULE PROPERTY]\n%s\n\t\"\"\"\n\t' % doc_lines,
        invocation=invocation
    )


# ----------------------------------------------------------------------------------------------------------------------
def generate_var_api(parent_name, var_name):
    template = """@property\ndef {function_name}(self):\n\t{invocation}\n"""
    invocation = 'return %s.%s' % (parent_name, var_name)
    return template.format(
        function_name=var_name,
        invocation=invocation
    )


# ----------------------------------------------------------------------------------------------------------------------
def generate_api(module, output_file, proxy_class_name):
    fns, cls, mods, _vars = get_api_parts(module)

    # -- start building content
    content = ''

    # -- write functions
    for fn_obj in fns:
        template_str = generate_function_api(fn_obj, 'self.proxy')
        if not template_str:
            continue
        content += '%s\n' % template_str

    for cls_obj in cls:
        template_str = generate_class_api('self.proxy', cls_obj)
        if not template_str:
            continue
        content += '%s\n' % template_str

    for mod_obj in mods:
        template_str = generate_module_api('self.proxy', module.__name__, mod_obj)
        if not template_str:
            continue
        content += '%s\n' % template_str

    for var_obj in _vars:
        template_str = generate_var_api('self.proxy', var_obj)
        if not template_str:
            continue
        content += '%s\n' % template_str

    header = 'class %sProxyWrapper(object):\n\n\tdef __init__(self, module_proxy):\n\t\tself.proxy = module_proxy'
    header += '\n\n'
    header = header % proxy_class_name

    content = indent(content)
    content = header + content

    with open(output_file, 'w+') as fp:
        fp.write(content)
