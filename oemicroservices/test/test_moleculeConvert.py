# Apache License 2.0
#
# Copyright (c) 2015-2016 Scott Arne Johnson
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
import base64

from openeye.oechem import *

from oemicroservices.common.util import compress_string, inflate_string
from oemicroservices.api import app

# Define the resource files relative to this test file because setup.py will run from the root package directory
# but some IDEs will run the tests from within the tests directory. We can be friendly to everybody.
LIGAND_FILE = os.path.join(os.path.dirname(__file__), 'assets/suv.pdb')


class TestMoleculeConvert(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_json_no_molecule_data(self):
        """
        Test JSON POST missing molecule data
        """
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"x": {"x": "x"}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No molecule information provided"}', response.data.decode("utf-8"))

    def test_json_no_input_data(self):
        """
        Test JSON POST missing all input molecule data
        """
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule": {"value": "x", "m": {"format": "z"}, "output": {"format": "x"}}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No input information provided"}', response.data.decode("utf-8"))

    def test_json_no_input_format(self):
        """
        Test JSON POST missing input molecule format
        """
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule": {"value": "x", "input": {"y": "z"}, "output": {"format": "x"}}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No input format provided"}', response.data.decode("utf-8"))

    def test_json_no_output_data(self):
        """
        Test JSON POST missing all output molecule data
        """
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule": {"value": "x", "input": {"format": "z"}, "x": {"format": "x"}}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No output information provided"}', response.data.decode("utf-8"))

    def test_json_no_output_format(self):
        """
        Test JSON POST missing output molecule format
        """
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule": {"value": "x", "input": {"format": "z"}, "output": {"p": "x"}}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("400 BAD REQUEST", response.status)
        self.assertEqual('{"error": "No output format provided"}', response.data.decode("utf-8"))

    def test_pdb_to_sdf(self):
        """
        Test PDB to SDF conversion
        """
        # First perform the conversion using the toolktis here
        reference = OEGraphMol()
        ifs = oemolistream(LIGAND_FILE)
        OEReadMolecule(ifs, reference)

        # Read the ligand as a string to POST
        with open(LIGAND_FILE, 'r') as f:
            target = f.read()

        # Perform the conversion to SDF
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule": {"value": target, "input": {"format": "pdb"}, "output": {"format": "sdf"}}}),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("200 OK", response.status, response.data)

        # Test the output schema
        payload = json.loads(response.data.decode('utf-8'))
        self.assertIn('molecule', payload)
        self.assertIn('value', payload['molecule'])
        self.assertIn('gz', payload['molecule'])

        # Write the ligand directly to a string
        ofs = oemolostream()
        ofs.SetFormat(OEFormat_SDF)
        ofs.openstring()
        OEWriteMolecule(ofs, reference)

        # Test the validity of the output molecule
        mol = OEGraphMol()
        ifs = oemolistream()
        ifs.SetFormat(OEFormat_SDF)
        self.assertTrue(ifs.openstring(payload['molecule']['value']))
        self.assertTrue(ifs.IsValid())
        self.assertTrue(OEReadMolecule(ifs, mol))
        self.assertTrue(mol.IsValid())

        # Test that the two molecule strings are equal
        self.assertEqual(ofs.GetString().decode('utf-8'), payload['molecule']['value'])

    def test_pdb_gz_to_sdf_gz(self):
        """
        Test PDB to SDF molecule conversion with gzipped and base64 encoded molecule in both input and output
        """
        # First perform the conversion using the toolktis here
        reference = OEGraphMol()
        ifs = oemolistream(LIGAND_FILE)
        OEReadMolecule(ifs, reference)

        # Read the ligand as a string to POST
        with open(LIGAND_FILE, 'r') as f:
            target = f.read()

        # Perform the conversion to SDF
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps(
                {
                    "molecule": {
                        "value": compress_string(target),
                        "input": {"format": "pdb", "gz": True},
                        "output": {"format": "sdf", "gz": True}
                    }
                }
            ),
            headers={"content-type": "application/json"}
        )
        # Test response status
        self.assertEqual("200 OK", response.status)

        # Test the output schema
        payload = json.loads(response.data.decode('utf-8'))
        self.assertIn('molecule', payload)
        self.assertIn('value', payload['molecule'])
        self.assertIn('gz', payload['molecule'])

        # Test the validity of the output molecule
        mol = OEGraphMol()
        ifs = oemolistream()
        ifs.SetFormat(OEFormat_SDF)
        self.assertTrue(ifs.openstring(inflate_string(payload['molecule']['value'])))
        self.assertTrue(ifs.IsValid())
        self.assertTrue(OEReadMolecule(ifs, mol))
        self.assertTrue(mol.IsValid())

        # Test that the two molecule strings are equal
        self.assertEqual(OECreateCanSmiString(reference), OECreateCanSmiString(mol))

    def test_smi_to_cdx(self):
        """
        Test SMI to CDX conversion
        """
        smiles = "Fc1cc(c(F)cc1F)C[C@@H](N)CC(=O)N3Cc2nnc(n2CC3)C(F)(F)F"
        # Perform the conversion to CDX
        response = self.app.post(
            '/v1/convert/molecule',
            data=json.dumps({"molecule":
                             {"value": smiles,
                              "input": {"format": "smi"},
                              "output": {"format": "cdx"}
                              }
                             }),
            headers={"content-type": "application/json"}
        )
        self.assertEqual("200 OK", response.status, response.data)

        # Test the output schema
        payload = json.loads(response.data.decode('utf-8'))
        self.assertIn('molecule', payload)
        self.assertIn('value', payload['molecule'])
        self.assertIn('gz', payload['molecule'])

        # read the CDX file back into OEMol
        cdx_data = base64.b64decode(payload['molecule']['value'])
        converted_mol = OEMol()
        self.assertTrue(OEReadMolFromBytes(converted_mol, ".cdx", cdx_data))

        # parse the reference smiles into OEMol
        smiles_mol = OEMol()
        self.assertTrue(OESmilesToMol(smiles_mol, smiles))

        self.assertEquals(OEMolToSmiles(smiles_mol), OEMolToSmiles(converted_mol))


