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

from oemicroservices.resources.depict.base import depictor_base_arg_parser
from oemicroservices.common.util import (
    render_error_image,
    get_image_mime_type,
    get_color_from_rgba,
    get_title_location,
    get_highlight_style,
    read_molecule_from_string)

########################################################################################################################
#                                                                                                                      #
#                                        Molecule depictor argument parser                                             #
#                                                                                                                      #
########################################################################################################################

# Extend the standard image_parser
depictor_arg_parser = depictor_base_arg_parser.copy()
# The image width
depictor_arg_parser.add_argument('width', type=int, default=400, location='args')
# The image height
depictor_arg_parser.add_argument('height', type=int, default=400, location='args')
# Substructure to highlight (multiple values allowed)
depictor_arg_parser.add_argument('highlight', type=str, action='append', location='args')
# Hex code for coloring the substructure
depictor_arg_parser.add_argument('highlightcolor',  type=str, default='#7070FF', location='args')
# Style in which to render the highlighted substructure
depictor_arg_parser.add_argument('highlightstyle',  type=str, default='default', location='args')
# Only for GET: the molecule string
depictor_arg_parser.add_argument('val', type=str, location='args')

########################################################################################################################
#                                                                                                                      #
#                                                  MoleculeDepictor                                                    #
#                                    RESTful resource for depicting small molecules                                    #
#                                                                                                                      #
########################################################################################################################


class MoleculeDepictor(Resource):
    """
    Render a small molecule in 2D
    """

    def __init__(self):
        # Initialize superclass
        super(MoleculeDepictor, self).__init__()

    def get(self, fmt):
        """
        Render an image with the molecule passed through the URL
        :param fmt: The image format
        :type fmt: str
        :return: The rendered image
        :rtype: Response
        """
        # Parse the query options
        args = depictor_arg_parser.parse_args()
        try:
            # Read the molecule
            mol = read_molecule_from_string(args['val'], fmt, bool(args['gz']), bool(args['reparse']))
            # Render the image
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return render_error_image(args['width'], args['height'], str(ex))

    def post(self, fmt):
        """
        Render an image with the molecule POST'ed to this resource
        :param fmt: The molecule format
        :type fmt: str
        :return: The rendered image
        :rtype: Response
        """
        # Parse the query options
        args = depictor_arg_parser.parse_args()
        try:
            # Read the molecule
            mol = read_molecule_from_string(request.data.decode("utf-8"), fmt, bool(args['gz']), bool(args['reparse']))
            # Render the image
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return render_error_image(args['width'], args['height'], str(ex))

    # noinspection PyMethodMayBeStatic
    def __render_image(self, mol, args):
        """
        Render a small molecule image
        :param mol: The molecule
        :param args: The parsed URL query string dictionary
        :return: A Flask Response with the rendered image
        :rtype: Response
        """
        # *********************************************************************
        # *                      Parse Parameters                             *
        # *********************************************************************
        width = args['width']                                          # Image width
        height = args['height']                                        # Image height
        title = args['title']                                          # Image title
        use_molecule_title = bool(args['keeptitle'])                   # Use the molecule title in the molecule file
        bond_scaling = bool(args['scalebonds'])                        # Bond width scales with size
        image_format = args['format']                                  # The output image format
        image_mimetype = get_image_mime_type(image_format)             # MIME type corresponding to the image format
        highlight_style = get_highlight_style(args['highlightstyle'])  # The substructure highlights style
        title_location = get_title_location(args['titleloc'])          # The title location (if we have a title)
        highlight = args['highlight']                                  # SMARTS substructures to highlight
        background = get_color_from_rgba(args['background'])           # Background color
        color = get_color_from_rgba(args['highlightcolor'])            # Highlight color

        # Make sure we got valid inputs
        if not image_mimetype:
            raise Exception("Invalid MIME type")

        # Defaults for invalid inputs
        if not highlight_style:
            highlight_style = OEHighlightStyle_Default

        if not title_location:
            title_location = OETitleLocation_Top
        # *********************************************************************
        # *                      Create the Image                             *
        # *********************************************************************
        image = OEImage(width, height)
        # Prepare the depiction
        OEPrepareDepiction(mol, False, True)
        opts = OE2DMolDisplayOptions(image.GetWidth(), image.GetHeight(), OEScale_AutoScale)

        # If we provided a title
        if title:
            mol.SetTitle(title)
            opts.SetTitleLocation(title_location)
        # Else hide if we didn't provide a title and we're *not* using the molecule title
        elif not use_molecule_title:
            mol.SetTitle("")
            opts.SetTitleLocation(OETitleLocation_Hidden)

        # Other configuration options
        opts.SetBondWidthScaling(bond_scaling)
        opts.SetBackgroundColor(background)

        # Prepare the display
        disp = OE2DMolDisplay(mol, opts)

        # Do any substructure matching
        if highlight:
            for querySmiles in highlight:
                subs = OESubSearch(querySmiles)
                for match in subs.Match(mol, True):
                    OEAddHighlighting(disp, color, highlight_style, match)

        # Render the image
        OERenderMolecule(image, disp)

        # Return the image in the response
        img_content = OEWriteImageToString(image_format, image)
        return Response(img_content, mimetype=image_mimetype)
