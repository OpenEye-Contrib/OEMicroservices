# Apache License 2.0
#
# Copyright (c) 2015 Scott Arne Johnson
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the LICENSE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from setuptools import setup

setup(
    name='OEMicroservices',
    version='1.3',
    packages=['oemicroservices', 'oemicroservices.test', 'oemicroservices.common', 'oemicroservices.resources',
              'oemicroservices.resources.depict', 'oemicroservices.resources.convert'],
    url='https://github.com/OpenEye-Contrib/OEMicroservices',
    license='MIT',
    author='Scott Arne Johnson',
    author_email='scott.johnson6@merck.com',
    description='Collection of useful microservices using the OpenEye toolkits',
    test_suite='oemicroservices.test',
    install_requires=['flask', 'flask-restful', 'marshmallow'],
    tests_require=['scikit-image']
)
