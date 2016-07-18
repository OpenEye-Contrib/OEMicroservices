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

from oemicroservices.common.util import make_response_from_error_dict

from flask_restful import Resource
from flask_restful import request
from flask import Response

from openeye.oechem import *

from marshmallow import Schema, fields

########################################################################################################################
#                                                                                                                      #
#                                                 MoleculeConvert                                                      #
#                                       Convert between molecule file formats                                          #
#                                                                                                                      #                                                                                    #
########################################################################################################################

class MoleculeConvertRequest(Schema):
    molecule = fields.String(required=True, validate=lambda s: s is not None and len(s) > 0)
    ifmt = fields.String(required=True, validate=lambda f: OEIsReadable(f),
                            error_messages={u'validator_failed': 'Unreadable input molecule format'})
    ofmt = fields.String(required=True, validate=lambda f:OEIsWriteable(f),
                            error_messages={u'validator_failed': 'Unreadable output molecule format'})
    igz = fields.Boolean(required=False, missing=False)
    ogz = fields.Boolean(required=False, missing=False)

class MoleculeConvert(Resource):
    """
    Convert between molecule file formats
    """

    def __init__(self):
        # Initialize superclass
        super(MoleculeConvert, self).__init__()

    def get(self):
        # Get the args from only the query string
        conversion = MoleculeConvertRequest().load( request.args.to_dict() )
        if conversion.errors:
            response = make_response_from_error_dict(conversion.errors)
        else:
            response = self.convert(conversion.data)
        return response

    def post(self):
        """
        Convert a molecule to another file format
        :return: A Flask Response with the rendered image
        :rtype: Response
        """
        # Get the args from both the query string and the JSON post body
        conversion = MoleculeConvertRequest().load( request.values.to_dict() )
        if conversion.errors:
            response = make_response_from_error_dict(conversion.errors)
        else:
            response = self.convert(conversion.data)
        return response

    def convert(self, params):
        """
        Convert a molecule from one format to another.
        :param params: The parameters as a MoleculeConvertRequest schema
        :return: A Flask response with either the converted molecules or an error
        """
        mol = OEGraphMol()
        try:
            # Read the input molecule
            OEReadMolFromBytes(mol, OEGetFileType(params['iformat']), params['igz'], params['molecule'])
            if not mol.IsValid():
                raise Exception("Invalid molecule")
            # Handle the reponse headers
            filename = "converted.{}".format(params['oformat'])
            if params['ogz']:
                mimetype = 'application/x-gzip'
                filename += '.gz'
            elif params['oformat'] == 'oeb':
                mimetype = 'application/octet-stream'
            else:
                mimetype = 'text/plain'
            # Convert and create the response
            return Response(
                OEWriteMolToBytes(OEGetFileType(params['oformat']), params['ogz'], mol),
                headers={'Content-Disposition': "attachment; filename={}".format(filename)},
                status=200,
                mimetype=mimetype,
            )
        except Exception as ex:
            return make_response_from_error_dict({"Error during conversion": str(ex)})

