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

import json
# noinspection PyUnresolvedReferences
import sys
import base64

from flask.ext.restful import Resource, request
from flask import Response
from openeye.oechem import *

from oemicroservices.common.util import compress_string, read_molecule_from_string

############################
# Python 2/3 Compatibility #
############################

# To support unicode as UTF-8 in Python 2 and 3
if sys.version_info < (3,):
    def to_utf8(u):
        return u.encode('utf-8')
else:
    def to_utf8(u):
        return u

########################################################################################################################
#                                                                                                                      #
#                                                 MoleculeConvert                                                      #
#                                       Convert between molecule file formats                                          #
#                                                                                                                      #
# Expects a POST:                                                                                                      #
#                                                                                                                      #
# {                                                                                                                    #
#   molecule: {                                                                                                        #
#     value:        A string that contains the molecule file string (*Required)                                        #
#     input : {                                                                                                        #
#       format:     The file format of the input molecule string (e.g. sdf, pdb, oeb, etc.) (*Required)                #
#       gz:         If the input molecule string is gzip + b64 encoded                                                 #
#     },                                                                                                               #
#     output: {                                                                                                        #
#       format:     The file format of the output molecule string (e.g. sdf, pdb, oeb, etc.) (*Required)               #
#       gz:         If the output molecule string should be gzip + b64 encoded                                         #
#     }                                                                                                                #
#   }                                                                                                                  #
# }                                                                                                                    #
#                                                                                                                      #
# Returns the following:                                                                                               #
#                                                                                                                      #
# {                                                                                                                    #
#   molecule: {                                                                                                        #
#       value:      A string containing the output molecule file string                                                #
#       format:     The output file format                                                                             #
#       gz:         If the output molecule string is gzip + b64 encoded                                                #
#   }                                                                                                                  #
# }                                                                                                                    #
########################################################################################################################

def is_gzip(payload):
    return bool('gz' in payload['molecule']['output'] and payload['molecule']['output']['gz'])

class MoleculeConvert(Resource):
    """
    Convert between molecule file formats
    """

    def __init__(self):
        # Initialize superclass
        super(MoleculeConvert, self).__init__()

    # noinspection PyMethodMayBeStatic
    def __validate_schema(self, obj):
        """
        Validate schema for JSON POST'ed to the resource
        :param obj: The parsed JSON object POST'ed to this resource
        """
        if not obj:
            raise Exception("No POST data received")
        if not isinstance(obj, dict):
            raise Exception("Unexpected POST data received")
        if 'molecule' not in obj:
            raise Exception("No molecule information provided")
        if 'value' not in obj['molecule']:
            raise Exception("No molecule file provided")
        if 'input' not in obj['molecule']:
            raise Exception("No input information provided")
        if 'format' not in obj['molecule']['input']:
            raise Exception("No input format provided")
        if 'output' not in obj['molecule']:
            raise Exception("No output information provided")
        if 'format' not in obj['molecule']['output']:
            raise Exception("No output format provided")

    def post(self):
        """
        Convert a molecule to another file format
        :return: A Flask Response with the rendered image
        :rtype: Response
        """
        # Parse the query options
        try:
            # We expect a JSON object in request.data with the protein and ligand data structures
            payload = json.loads(request.data.decode("utf-8"))
            # Checks to make sure we have everything we need in payload
            self.__validate_schema(payload)
            # Read the molecule
            mol = read_molecule_from_string(
                payload['molecule']['value'],
                payload['molecule']['input']['format'],
                payload['molecule']['input']['gz'] if 'gz' in payload['molecule']['input'] else False,
                payload['molecule']['input']['reparse'] if 'reparse' in payload['molecule']['input'] else False
            )

            # Prepare the molecule for writing
            ofs_format = payload['molecule']['output']['format']
            if ofs_format == "smiles":
                ofs_format = ".smi"

            format_type = OEGetFileType(ofs_format)
            if format_type == OEFormat_UNDEFINED:
                raise Exception("Unknown output file type: " + format)

            if is_gzip(payload):
                ofs_format += ".gz"
            output = OEWriteMolToBytes(ofs_format, mol)

            if OEIsBinary(format_type) or is_gzip(payload):
                output = base64.b64encode(output)
            output = output.decode("utf-8")

            return Response(json.dumps(
                {
                    'molecule': {
                        'value': output,
                        'format': payload['molecule']['output']['format'],
                        'gz': is_gzip(payload)
                    }
                }
            ), status=200, mimetype='application/json')

        except Exception as ex:
            return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
