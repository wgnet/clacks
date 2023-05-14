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
import setuptools

with open('readme.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='clacks',
    version='0.0.1',
    author='Mattias Van Camp',
    author_email='mavcart.mvc@gmail.com',
    description='Modular TCP Server framework to make it easy to create remote APIs for tech artists.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/MaVCArt/clacks',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache 2.0 License',
        'Operating System :: OS Independent',
    ],
)
