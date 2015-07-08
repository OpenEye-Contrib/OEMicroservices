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
import json
import os

from oemicroservices.common.util import compress_string
from oemicroservices.api import app

# Define the resource files relative to this test file because setup.py will run from the root package directory
# but some IDEs will run the tests from within the tests directory. We can be friendly to everybody.
PDB_FILE = os.path.join(os.path.dirname(__file__), 'assets/4s0v.pdb')
LIGAND_FILE = os.path.join(os.path.dirname(__file__), 'assets/suv.pdb')
RECEPTOR_FILE = os.path.join(os.path.dirname(__file__), 'assets/receptor.pdb')

# TODO Implement image comparison tests - rendering occurs differently on each platform, so must use similarity


class TestInteractionDepictor(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_json_no_ligand_data(self):
        """
        Test JSON POST missing all ligand data
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"x": {"value": "x", "format": "x"}, "receptor": {"value": "x", "format": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No ligand data provided in POST"}', response.data.decode("utf-8"))

    def test_json_no_ligand_file(self):
        """
        Test JSON POST missing ligand file
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"ligand": {"x": "x", "gz": "1"}, "receptor": {"value": "x", "format": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No value for ligand file provided in POST"}', response.data.decode("utf-8"))

    def test_json_no_ligand_format(self):
        """
        Test JSON POST missing ligand format
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"ligand": {"value": "x", "x": "x"}, "receptor": {"value": "x", "format": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No format for ligand file provided in POST"}', response.data.decode("utf-8"))

    def test_json_no_receptor_data(self):
        """
        Test JSON POST missing all receptor data
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"ligand": {"value": "x", "format": "x"}, "x": {"value": "x", "format": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No receptor data provided in POST"}', response.data.decode("utf-8"))

    def test_json_no_receptor_file(self):
        """
        Test JSON POST missing receptor file
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"ligand": {"value": "x", "format": "x"}, "receptor": {"x": "x", "format": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No value for receptor file provided in POST"}', response.data.decode("utf-8"))

    def test_json_no_receptor_format(self):
        """
        Test JSON POST missing receptor format
        """
        response = self.app.post(
            '/v1/depict/interaction?format=svg&debug=true',
            data=json.dumps({"ligand": {"value": "x", "format": "x"}, "receptor": {"value": "x", "x": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No format for receptor file provided in POST"}', response.data.decode("utf-8"))

    def test_interaction_success(self):
        """
        Test creating a simple ligand-receptor interaction map
        """
        # Read the protein and ligand
        with open(LIGAND_FILE, 'r') as f:
            ligand = f.read()
        with open(RECEPTOR_FILE, 'r') as f:
            receptor = f.read()
        # POST in JSON
        response = self.app.post(
            '/v1/depict/interaction?format=png&debug=true',
            data=json.dumps(
                {"ligand": {"value": ligand, "format": "pdb"}, "receptor": {"value": receptor, "format": "pdb"}}
            ),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("200 OK", response.status)

    def test_invalid_file_format(self):
        """
        Test providing an invalid file format for the molecule
        """
        # Read the protein and ligand
        with open(LIGAND_FILE, 'r') as f:
            ligand = f.read()
        with open(RECEPTOR_FILE, 'r') as f:
            receptor = f.read()
        # POST in JSON
        response = self.app.post(
            '/v1/depict/interaction?format=png&debug=true',
            data=json.dumps(
                {"ligand": {"value": ligand, "format": "invalid"}, "receptor": {"value": receptor, "format": "pdb"}}
            ),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "Error reading ligand: Invalid molecule format: invalid"}',
                         response.data.decode('utf-8'))

    def test_interaction_b64_ligand(self):
        """
        Test providing a gzipped and then base64 encoded ligand
        """
        # Read the protein and ligand
        with open(LIGAND_FILE, 'r') as f:
            ligand = f.read()
        with open(RECEPTOR_FILE, 'r') as f:
            receptor = f.read()
        # POST in JSON
        response = self.app.post(
            '/v1/depict/interaction?format=png&debug=true',
            data=json.dumps(
                {
                    "ligand": {"value": compress_string(ligand), "format": "pdb", "gz": True},
                    "receptor": {"value": receptor, "format": "pdb"}
                }
            ),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("200 OK", response.status)

    def test_interaction_b64_protein(self):
        """
        Test providing a gzipped and then base64 encoded receptor
        """
        # Read the protein and ligand
        with open(LIGAND_FILE, 'r') as f:
            ligand = f.read()
        with open(RECEPTOR_FILE, 'r') as f:
            receptor = f.read()
        # POST in JSON
        response = self.app.post(
            '/v1/depict/interaction?format=png&debug=true',
            data=json.dumps(
                {
                    "ligand": {"value": ligand, "format": "pdb"},
                    "receptor": {"value": compress_string(receptor), "format": "pdb", "gz": True}
                }
            ),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("200 OK", response.status)

    def test_find_ligand_resn_success(self):
        """
        Test POSTing a single molecule file and then finding the ligand based on residue name
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resn=SUV',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("200 OK", response.status)

    def test_find_ligand_chain_success(self):
        """
        Test POSTing a single molecule file and then finding the ligand based on chain ID
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&chain=B',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("200 OK", response.status)

    def test_find_ligand_resi_success(self):
        """
        Test POSTing a single molecule file and then finding the ligand based on residue number
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resi=2001',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("200 OK", response.status)

    def test_find_ligand_complex_success(self):
        """
        Test POSTing a single molecule file and then finding the ligand based on a complex query using residue name,
        residue number and chain ID
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resi=2001&chain=B&resn=SUV',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("200 OK", response.status)

    def test_find_ligand_resn_fail(self):
        """
        Test providing an invalid residue name
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resn=XXX',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No atoms matched ligand selection"}', response.data.decode('utf-8'))

    def test_find_ligand_resi_fail(self):
        """
        Test providing an invalid residue number
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resn=999',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No atoms matched ligand selection"}', response.data.decode('utf-8'))

    def test_find_ligand_chain_fail(self):
        """
        Test providing an invalid chain ID
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&chain=X',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No atoms matched ligand selection"}', response.data.decode('utf-8'))

    def test_find_ligand_complex_fail(self):
        """
        Test providing an invalid complex query
        """
        # Read combined protein and ligand file
        with open(PDB_FILE, 'r') as f:
            pdb = f.read()
        # POST the pdb file and search for the SUV residue name
        response = self.app.post(
            '/v1/depict/interaction/search/pdb?format=png&debug=true&resi=2001&chain=X&resn=SUV',
            data=pdb,
            headers={"content-type": "text/plain"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No atoms matched ligand selection"}', response.data.decode('utf-8'))
