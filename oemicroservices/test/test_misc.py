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

from openeye.oechem import *

from oemicroservices.common.functor import generate_ligand_functor

# Define the resource files relative to this test file because setup.py will run from the root package directory
# but some IDEs will run the tests from within the tests directory. We can be friendly to everybody.
PDB_FILE = os.path.join(os.path.dirname(__file__), 'assets/4s0v.pdb')


class TestInteractionDepictor(TestCase):
    def test_generate_ligand_functor(self):
        """
        Test generating a simple ligand functor
        """
        # Read the molecule
        mol = OEGraphMol()
        ifs = oemolistream(PDB_FILE)
        OEReadMolecule(ifs, mol)
        # Generate the taxol functor
        functor = generate_ligand_functor(resn='SUV')
        self.assertEqual(55, OECount(mol, functor), 'Count residue atoms with functor')
