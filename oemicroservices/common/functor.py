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

from openeye.oechem import *
from openeye.oedepict import *

class OEHasResidueName(OEUnaryAtomPred):
    """
    Predicate functor to get atoms with a specific residue name
    """
    def __init__(self, resn):
        """
        Default constructor
        :param resn: The residue name
        :type resn: str
        :return:
        """
        OEUnaryAtomPred.__init__(self)
        self.resn = resn

    def __call__(self, atom):
        """
        Automatically called on each atom in an OEMol
        :param atom: The atom the functor is evaluating
        :type atom: OEAtomBase
        :return: True if the functor evaluates to true
        """
        res = OEAtomGetResidue(atom)
        return res.GetName() == self.resn

    def CreateCopy(self):
        # __disown__ is required to allow C++ to take ownership of this
        # object and its memory
        return OEHasResidueName(self.resn).__disown__()


def generate_ligand_functor(chain=None, resi=None, resn=None):
    """
    Generate the predicate functor to select the ligand atoms out of the
    protein-ligand complex. This should be called with at least one
    of the parameters not None.
    :param chain: The chain ID of the ligand
    :type chain: str
    :param resi: The residue number of the ligand
    "type resi: int
    :param resn: The residue name of the ligand
    :type resn: str
    :return: A functor for selecting a ligand
    :rtype: OEUnaryAtomPred
    """
    functor = OEIsTrueAtom()
    # If we got a chain ID
    if chain is not None:
        functor = OEAndAtom(functor, OEHasChainID(ord(chain[0])))
    # If we got a residue number
    if resi is not None:
        functor = OEAndAtom(functor, OEHasResidueNumber(int(resi)))
    # If we got a residue name
    if resn is not None:
        functor = OEAndAtom(functor, OEHasResidueName(resn))
    return functor


class ApplyAtomLabels(OEDisplayAtomPropBase):
    """
    Functor for assigning atom labels by atom index using a dictionary of {index: label pairs}, e.g. {1:"label", ...}
    :param atom_labels: a dict of OE labels where the keys are the atom index (ints) and the values are the atom labels
        :param index_start: the starting atom index as an integer (0 or 1)
    :type: dict
    """
    def __init__(self, atom_labels, index_start):
        OEDisplayAtomPropBase.__init__(self)
        self.atom_labels = atom_labels
        self.index_start = index_start

    def __call__(self, atom):
        if atom.GetIdx() + self.index_start in self.atom_labels:
            return self.atom_labels[atom.GetIdx() + self.index_start]
        return ""

    def CreateCopy(self):
        # __disown__ is required to allow C++ to take
        # ownership of this object and its memory
        copy = ApplyAtomLabels(self.atom_labels, self.index_start)
        return copy.__disown__()


class ApplyBondLabels(OEDisplayBondPropBase):
    """
    Functor for assigning bond labels by bond index using a dictionary of {index: label pairs}, e.g. {1:"label", ...}
    :param bond_labels: a dict of OE labels where the keys are the bond index (ints) and the values are the bond labels
    :param index_start: the starting atom index as an integer (0 or 1)
    :type: dict
    """
    def __init__(self, bond_labels, index_start):
        OEDisplayBondPropBase.__init__(self)
        self.bond_labels = bond_labels
        self.index_start = index_start

    def __call__(self, bond):
        if bond.GetIdx() + self.index_start in self.bond_labels:
            return self.bond_labels[bond.GetIdx() + self.index_start]
        return ""

    def CreateCopy(self):
        # __disown__ is required to allow C++ to take
        # ownership of this object and its memory
        copy = ApplyBondLabels(self.bond_labels, self.index_start)
        return copy.__disown__()