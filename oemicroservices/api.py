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

from flask import Flask
from flask.ext.restful import Api

from oemicroservices.resources.depict.interaction import InteractionDepictor, FindLigandInteractionDepictor
from oemicroservices.resources.convert.convert import MoleculeConvert
from oemicroservices.resources.depict.molecule import MoleculeDepictor

app = Flask(__name__)
api = Api(app)

###############################################################################
# Molecule depiction resources                                                #
###############################################################################
# Depict a small molecule
api.add_resource(MoleculeDepictor, '/v1/depict/structure/<string:fmt>')
# Depict a receptor-ligand complex
api.add_resource(InteractionDepictor, '/v1/depict/interaction')
# Depict a receptor-ligand complex by first searching for the ligand in the raw file
api.add_resource(FindLigandInteractionDepictor, '/v1/depict/interaction/search/<string:fmt>')
# Convert between molecule formats
api.add_resource(MoleculeConvert, '/v1/convert/molecule')
