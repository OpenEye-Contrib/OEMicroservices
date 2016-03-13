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

import json

from flask.ext.restful import Resource, request
from flask import Response
from openeye.oechem import *
from openeye.oedepict import *
from openeye.oegrapheme import *

from openeye.oedocking import *

from oemicroservices.resources.depict.base import depictor_base_arg_parser_v1
from oemicroservices.common.functor import generate_ligand_functor
from oemicroservices.common.util import (
    render_error_image,
    get_image_mime_type,
    get_color_from_rgba,
    get_title_location,
    read_molecule_from_string)

########################################################################################################################
#                                                                                                                      #
#                                        Molecule depictor argument parser                                             #
#                                                                                                                      #
########################################################################################################################

# Extend the standard image_parser
interaction_arg_parser = depictor_base_arg_parser_v1.copy()
# The image width
interaction_arg_parser.add_argument('width', type=int, default=800, location='args')
# The image height
interaction_arg_parser.add_argument('height', type=int, default=600, location='args')
# Include a legend with the image
interaction_arg_parser.add_argument('legend', type=bool, default=True, location='args')

# Parameters for POST: Find the ligand
interaction_arg_parser.add_argument('chain', type=str, location='args')  # Ligand chain ID
interaction_arg_parser.add_argument('resi', type=int, location='args')   # Ligand residue number
interaction_arg_parser.add_argument('resn', type=str, location='args')   # Ligand residue name

########################################################################################################################
#                                                                                                                      #
#                                                  Utility Functions                                                   #
#                                                                                                                      #
########################################################################################################################


def _render_image(receptor, ligand, args):
    """
    Render a receptor-ligand interaction image
    :param receptor: The receptor
    :type receptor OEMol
    :param ligand: The bound ligand
    :type ligand: OEMol
    :param args: The parsed URL query string dictionary
    :type args: dict
    :return: A Flask Response with the rendered image
    :rtype: Response
    """
    # *********************************************************************
    # *                      Parse Parameters                             *
    # *********************************************************************
    width = args['width']                                       # Image width
    height = args['height']                                     # Image height
    title = args['title']                                       # Image title
    use_molecule_title = bool(args['keeptitle'])                # Use the molecule title in the molecule file
    bond_scaling = bool(args['scalebonds'])                      # Bond width scales with size
    image_format = args['format']                               # The output image format
    image_mimetype = get_image_mime_type(image_format)          # MIME type corresponding to the image format
    title_location = get_title_location(args['titleloc'])       # The OpenEye title location (if we have a title)
    legend = bool(args['legend'])                               # Display a legend
    background = get_color_from_rgba(args['background'])        # Background color

    # Make sure we got valid inputs
    if not image_mimetype:
        raise Exception("Invalid MIME type")

    if not title_location:
        title_location = OETitleLocation_Top
    # *********************************************************************
    # *                      Create the Image                             *
    # *********************************************************************
    image = OEImage(width, height)
    # Compute the image frame sizes
    cwidth = width if legend == 0 else 0.80 * width
    lwidth = width if legend == 0 else 0.20 * width
    loffset = 0.0 if legend == 0 else 0.8 * width
    cframe = OEImageFrame(image, cwidth, height, OE2DPoint(0.0, 0.0))
    lframe = OEImageFrame(image, lwidth, height, OE2DPoint(loffset, 0.0))
    # Prepare the depiction
    opts = OE2DActiveSiteDisplayOptions(cframe.GetWidth(), cframe.GetHeight())

    # Additional visualization options
    opts.SetBondWidthScaling(bond_scaling)
    opts.SetBackgroundColor(background)

    # Perceive interactions
    asite = OEFragmentNetwork(receptor, ligand)

    if not asite.IsValid():
        raise Exception("The active site is not valid")

    # Add optional title
    if title:
        asite.SetTitle(title)
        opts.SetTitleLocation(title_location)
    elif use_molecule_title:
        asite.SetTitle(ligand.GetTitle())
        opts.SetTitleLocation(title_location)
    else:
        asite.SetTitle("")
        opts.SetTitleLocation(OETitleLocation_Hidden)

    # Add interactions
    OEAddDockingInteractions(asite)
    OEPrepareActiveSiteDepiction(asite)

    # Render the active site
    adisp = OE2DActiveSiteDisplay(asite, opts)
    OERenderActiveSite(cframe, adisp)

    # Render the legend
    if args['legend'] != 0:
        lopts = OE2DActiveSiteLegendDisplayOptions(10, 1)
        OEDrawActiveSiteLegend(lframe, adisp, lopts)

    # Respond with the image
    img_content = OEWriteImageToString(image_format, image)
    return Response(img_content, mimetype=image_mimetype)

########################################################################################################################
#                                                                                                                      #
#                                                 InteractionDepictor                                                  #
#                                 Depict receptor-ligand interactions of pre-split molecules                           #
#                                                                                                                      #
# Expects a POST:                                                                                                      #
#                                                                                                                      #
# {                                                                                                                    #
#   ligand: {                                                                                                          #
#     value:  A string that contains the ligand structure                                                              #
#     format: The file format of the ligand string (e.g. sdf, pdb, oeb, etc.)                                          #
#     gz:     If the ligand string is gzipped and then b64 encoded                                                     #
#   },                                                                                                                 #
#   receptor: {                                                                                                        #
#     value:  A string that contains the receptor structure                                                            #
#     format: The file format of the receptor string (e.g. sdf, pdb, oeb, egc.)                                        #
#     gz:     If the receptor string is gzipped and then b64 encoded                                                   #
#   }                                                                                                                  #
# }                                                                                                                    #
#                                                                                                                      #
########################################################################################################################


class InteractionDepictor(Resource):
    """
    Generate a receptor-ligand interaction map given a receptor and ligand in a JSON object
    """

    def __init__(self):
        # Call the superclass initializers
        super(InteractionDepictor, self).__init__()

    # noinspection PyMethodMayBeStatic
    def __validate_schema(self, obj):
        """
        Validate schema for JSON POST'ed to the resource
        :param obj: The parsed JSON object
        """
        # Check data
        if not obj:
            raise Exception("No POST data received")
        if not isinstance(obj, dict):
            raise Exception("Unexpected POST data received")
        # Check ligand
        if 'ligand' not in obj:
            raise Exception("No ligand data provided in POST")
        if 'value' not in obj['ligand']:
            raise Exception("No value for ligand file provided in POST")
        if 'format' not in obj['ligand']:
            raise Exception("No format for ligand file provided in POST")
        # Check receptor
        if 'receptor' not in obj:
            raise Exception("No receptor data provided in POST")
        if 'value' not in obj['receptor']:
            raise Exception("No value for receptor file provided in POST")
        if 'format' not in obj['receptor']:
            raise Exception("No format for receptor file provided in POST")

    def post(self):
        """
        Render JSON that has been POST'ed to this resource
        :return: A Flask Response with the rendered image
        :rtype: Response
        """
        # Parse the query options
        args = interaction_arg_parser.parse_args()
        try:
            # We exepct a JSON object in request.data with the protein and ligand data structures
            payload = json.loads(request.data.decode("utf-8"))
            self.__validate_schema(payload)

            # Try to read the ligand from the payload
            try:
                ligand = read_molecule_from_string(
                    payload['ligand']['value'],
                    payload['ligand']['format'],
                    payload['ligand']['gz'] if 'gz' in payload['ligand'] else False,
                    args['reparse']
                )
            except Exception as ex:
                message = "Error reading ligand"
                if args['debug']:
                    message += ": {0}".format(str(ex))
                raise Exception(message)

            # Try to read the receptor from the payload
            try:
                receptor = read_molecule_from_string(
                    payload['receptor']['value'],
                    payload['receptor']['format'],
                    payload['receptor']['gz'] if 'gz' in payload['receptor'] else False,
                    args['reparse']
                )
            except Exception as ex:
                message = "Error reading receptor"
                if args['debug']:
                    message += ": {0}".format(str(ex))
                raise Exception(message)

            # Render the image
            return _render_image(receptor, ligand, args)

        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return render_error_image(args['width'], args['height'], str(ex))

########################################################################################################################
#                                                                                                                      #
#                                            FindLigandInteractionDepictor                                             #
#                      Finds the ligand within a complex and depicts the ligand-receptor interactions                  #
#                                                                                                                      #
# The POST is the raw ligand-receptor complex file string                                                              #
#                                                                                                                      #
########################################################################################################################


class FindLigandInteractionDepictor(Resource):
    """
    Generate a receptor-ligand interaction map given a receptor and ligand in a JSON object
    """

    def __init__(self):
        # Call the superclass initializers
        super(FindLigandInteractionDepictor, self).__init__()

    # noinspection PyMethodMayBeStatic
    def post(self, fmt):
        """
        Render a raw receptor-ligand that has been POST'ed to this resource by first searching for the ligand
        :return: A Flask Response with the rendered image
        :rtype: Response
        """
        # Parse the query options
        args = interaction_arg_parser.parse_args()
        try:
            # Try to read the receptor-ligand complex
            try:
                mol = read_molecule_from_string(
                    request.data.decode("utf-8"),
                    fmt,
                    args['gz'],
                    args['reparse']
                )
            except Exception as ex:
                message = "Error reading molecule file"
                if args['debug']:
                    message += ": {0}".format(str(ex))
                raise Exception(message)

            # Generate the ligand selection functor
            if args['chain'] or args['resi'] or args['resn']:
                functor = generate_ligand_functor(args['chain'], args['resi'], args['resn'])
            else:
                raise Exception("No ligand selection options given")

            # Split the ligand from the complex
            ligand = OEGraphMol()
            OESubsetMol(ligand, mol, functor, False, False)

            # Check the ligand
            if not ligand or ligand.NumAtoms() == 0:
                raise Exception("No atoms matched ligand selection")

            # Delete the ligand from the complex
            for atom in mol.GetAtoms(functor):
                mol.DeleteAtom(atom)

            # Error check receptor
            if not mol or mol.NumAtoms() == 0:
                raise Exception("No atoms in receptor")

            return _render_image(mol, ligand, args)

        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return render_error_image(args['width'], args['height'], str(ex))
