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

from unittest import TestCase
import os

try:
    # Python 3.x
    from urllib.parse import quote
except ImportError:
    # Python 2.x
    from urllib import quote

from oemicroservices.common.util import compress_string
from oemicroservices.api import app

# Define the resource files relative to this test file because setup.py will run from the root package directory
# but some IDEs will run the tests from within the tests directory. We can be friendly to everybody.
LIGAND_FILE = os.path.join(os.path.dirname(__file__), 'assets/suv.pdb')

# TODO Implement image comparison tests - rendering occurs differently on each platform, so must use similarity

########################################################################################################################
# API Version 1 Tests
########################################################################################################################


class TestMoleculeDepictorV1(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get_smiles_v1(self):
        response = self.app.get('/v1/depict/structure/smiles?val=c1ccccc1&debug=true')
        self.assertEqual("200 OK", response.status)

    def test_get_b64_smiles_v1(self):
        # Compress and encode
        url_compressed = quote(compress_string('c1ccccc1'))
        response = self.app.get('/v1/depict/structure/smiles?val={0}&debug=true&gz=true'.format(url_compressed))
        self.assertEqual("200 OK", response.status)

    def test_get_b64_pdb_v1(self):
        with open(LIGAND_FILE, 'r') as f:
            ligand = f.read()
        # Compress and encode
        url_compressed = quote(compress_string(ligand))
        response = self.app.get('/v1/depict/structure/pdb?val={0}&debug=true&gz=true'.format(url_compressed))
        self.assertEqual("200 OK", response.status)

    def test_invalid_file_format_v1(self):
        response = self.app.get('/v1/depict/structure/invalid?val=c1ccccc1&debug=true')
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "Invalid molecule format: invalid"}', response.data.decode('utf-8'))

    def test_get_b64_smiles_v2(self):
        # Compress and encode
        url_compressed = quote(compress_string('c1ccccc1'))
        url_string = '/v2/depict/structure/{0}?molecule-format=smiles&debug=true&gz=true'.format(url_compressed)
        response = self.app.get(url_string)
        self.assertEqual("200 OK", response.status)


########################################################################################################################
# API Version 2 Tests
########################################################################################################################


class TestMoleculeDepictorV2(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get_smiles_v2(self):
        response = self.app.get('/v2/depict/structure/c1ccccc1?molecule-format=smiles&debug=false')
        print(response)
        self.assertEqual("200 OK", response.status)

    # def test_get_b64_smiles_v2(self):
    #     # Compress and encode
    #     url_compressed = quote(compress_string('c1ccccc1'))
    #     url_string = '/v2/depict/structure/{0}?molecule-format=smiles&debug=true&gz=true'.format(url_compressed)
    #     response = self.app.get(url_string)
    #     self.assertEqual("200 OK", response.status)
    #
    # def test_get_b64_pdb_v2(self):
    #     with open(LIGAND_FILE, 'r') as f:
    #         ligand = f.read()
    #     # Compress and encode
    #     url_compressed = quote(compress_string(ligand))
    #     url_string = '/v2/depict/structure/{0}?molecule-format=pdb&debug=true&gz=true'.format(url_compressed)
    #     response = self.app.get(url_string)
    #     self.assertEqual("200 OK", response.status)

    def test_invalid_file_format_v2(self):
        response = self.app.get('/v2/depict/structure/c1ccccc1?molecule-format=invalid&debug=true')
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "Invalid molecule format: invalid"}', response.data.decode('utf-8'))