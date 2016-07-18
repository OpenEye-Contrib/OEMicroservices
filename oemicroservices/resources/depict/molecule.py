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

from flask_restful import Resource, request
from flask import Response
from openeye.oechem import *

from openeye.oedepict import *

from oemicroservices.resources.depict.schema import MoleculeDepctionRequest

# from oemicroservices.resources.depict.schema import depictor_base_arg_parser
from oemicroservices.common.functor import ApplyAtomLabels, ApplyBondLabels
import oemicroservices.common.util as util


def __create_base_image_and_opts(mol, args):
    """
    Creates the base molecule image shared by API v1 and v2 to avoid repeated code
    """
    image = OEImage(args['width'], args['height'])
    # Prepare the depiction
    OEPrepareDepiction(mol, False, True)
    opts = OE2DMolDisplayOptions(image.GetWidth(), image.GetHeight(), OEScale_AutoScale)
    # Defaults for API v2 which have no effect on API v1
    opts.SetAtomLabelFontScale(1.4)
    opts.SetAtomPropLabelFontScale(1.4)
    opts.SetBondPropLabelFontScale(1.4)
    # If we provided a title
    if args['title']:
        mol.SetTitle(args['title'])
        opts.SetTitleLocation(args['title-loc'])
    # Else if we are throwing out titles
    elif not args['keep-title']:
        mol.SetTitle("")
        opts.SetTitleLocation(OETitleLocation_Hidden)
    # FIXME If highlighting by cogwheel, can't use transparent background (error in OEDepict)
    if ('highlight-atoms' in args and args['highlight-atoms']) or ('highlight-ss' in args and args['highlight-ss']) \
            and (args['highlight-style'] == OEHighlightByCogwheel):
        args['background'].SetA(255)
    # Other configuration options
    opts.SetBondWidthScaling(args['bond-scaling'])
    opts.SetBackgroundColor(args['background'])
    return image, opts

    # if ('highlight-atoms' in args and args['highlight-atoms']) or ('highlight-ss' in args and args['highlight-ss']) and args['highlight-style'] == OEHighlightByCogwheel:
    #    background.SetA(255)

########################################################################################################################
#                                                                                                                      #
#                                                  MoleculeDepictor                                                    #
#                                    RESTful resource for depicting small molecules                                    #
#                                                      API v1                                                          #
#                                                                                                                      #
########################################################################################################################


class MoleculeDepictorV1(Resource):
    """
    Render a small molecule in 2D
    """

    def __init__(self):
        # Initialize superclass
        super(MoleculeDepictorV1, self).__init__()

    def get(self, fmt):
        """
        Render an image with the molecule passed through the URL
        :param fmt: The image format
        :type fmt: str
        :return: The rendered image
        :rtype: Response
        """
        # Parse the query options
        # args = self.depictor_arg_parser.parse_args()
        args = None
        try:
            # Read the molecule
            mol = OEGraphMol()
            OEReadMolFromBytes(mol, OEGetFileType(fmt), bool(args['gzip']), args['val'])
            # Render the image
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return util.render_error_image(args['width'], args['height'], str(ex))

    def post(self, fmt):
        """
        Render an image with the molecule POST'ed to this resource
        :param fmt: The molecule format
        :type fmt: str
        :return: The rendered image
        :rtype: Response
        """
        # Parse the query options
        args = self.depictor_arg_parser.parse_args()
        try:
            # Read the molecule
            mol = OEGraphMol()
            OEReadMolFromBytes(mol, OEGetFileType(fmt), bool(args['gzip']), args['val'])
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                return util.render_error_image(args['width'], args['height'], str(ex))

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
        image_mimetype = util.get_image_mime_type(image_format)        # MIME type corresponding to the image format
        highlight_style = util.get_highlight_style(args['highlightstyle'])  # The substructure highlights style
        title_location = util.get_title_location(args['titleloc'])     # The title location (if we have a title)
        highlight = args['highlight']                                  # SMARTS substructures to highlight
        background = util.get_color_from_rgba(args['background'])      # Background color
        color = util.get_color_from_rgba(args['highlightcolor'])       # Highlight color

        # Make sure we got valid inputs
        if not image_mimetype:
            raise Exception("Invalid MIME type")

        # Defaults for invalid inputs
        if not highlight_style:
            highlight_style = OEHighlightStyle_Default

        if not title_location:
            title_location = OETitleLocation_Top
        # Create the image
        image, opts = __create_base_image_and_opts(mol, args)
        # Prepare the display
        disp = OE2DMolDisplay(mol, opts)
        # Do any substructure matching and highlighting
        if args['highlight-ss']:
            for querySmiles in args['highlight-ss']:
                subs = OESubSearch(querySmiles)
                for match in subs.Match(mol, True):
                    OEAddHighlighting(disp, args['highlight-color'], args['highlight-style'], match)

        # Render the image
        OERenderMolecule(image, disp)

        # Return the image in the response
        img_content = OEWriteImageToString(image_format, image)
        return Response(img_content, mimetype=image_mimetype)

########################################################################################################################
#                                                                                                                      #
#                                                  MoleculeDepictor                                                    #
#                                    RESTful resource for depicting small molecules                                    #
#                                                                                                                      #
########################################################################################################################


class MoleculeDepictorV2(Resource):
    """
    Render a small molecule in 2D
    """



    def __init__(self):
        # Initialize superclass
        super(MoleculeDepictorV2, self).__init__()

    def get(self, molecule):
        """
        Render an image with the molecule passed through the URL
        :param molecule: The molecule string to be rendered
        :return: The rendered image
        :rtype: Response
        """
        size = (400, 400) # Width and height for error image in case exception is thrown
        try:
            # Process the query and JSON parameters
            params = util.combine_query_and_json_parameters(request)
            # Add the molecule in the URL path to the arguments
            params['molecule'] = molecule
            # Process all of the raw input parameters into sensible input arguments
            args = MoleculeDepctionRequest().load(params)
            # Get the size in case we thrown an exception
            size = (args.data['width'], args.data['height'])
            # If there were errors
            if args.errors:
                raise Exception(util.stringify_error_dict(args.errors))
            # Render the image with the processed arguments
            return self.__render_image(args.data)
        except Exception as ex:
            return util.render_error_image(size[0], size[1], str(ex))

        # # return Response(json.dumps(args), status=400, mimetype='application/json')
        # try:
        #     # Read the molecule
        #     mol = OEGraphMol()
        #     OEReadMolFromBytes(mol, OEGetFileType(args['molfmt']), bool(args['gzip']), molecule)
        #     # fix highlight-atoms sets coming from URL (comma-separated values to int list)
        #     args['highlight-atoms'] = util.fix_highlight_atoms_from_get(args['highlight-atoms'], args['index-start'])
        #     # Render the image
        #     return self.__render_image(mol, args)
        # # On error render a PNG with an error message
        # except Exception as ex:
        #     if args['debug']:
        #         return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
        #     else:
        #         return util.render_error_image(args['width'], args['height'], str(ex))

    def post(self, molecule=None):
        """
        Render an image with the molecule passed in the POST body
        :param molecule: The molecule string to be rendered
        :return: The rendered image
        :rtype: Response
        """
        size = (400, 400)  # Width and height for error image in case exception is thrown
        try:
            # Process the query and JSON parameters
            params = util.combine_query_and_json_parameters(request)
            # If no molecule was passed via JSON or in the query string then try to use the path
            if not 'molecule' in params and molecule:
                params['molecule'] = molecule
            # Process all of the raw input parameters into sensible input arguments
            args = MoleculeDepctionRequest().load(params)
            # Get the size in case we thrown an exception
            size = (args.data['width'], args.data['height'])
            # If there were errors
            if args.errors:
                raise Exception(util.stringify_error_dict(args.errors))
            # Render the image with the processed arguments
            return self.__render_image(args.data)
        except Exception as ex:
            return util.render_error_image(size[0], size[1], str(ex))
        #
        # """
        # Render an image with the molecule POST'ed to this resource
        # :param molecule: The molecule string to be rendered
        # :return: The rendered image
        # :rtype: Response
        # """
        # # Parse the query options
        # args = self.depictor_arg_parser.parse_args()
        # # if body is json, extract molecule from molecule field, otherwise assume that the body contains the molecule
        # if not molecule:
        #     if request.mimetype == 'application/json':
        #         if 'molecule' in args:
        #             molecule = args['molecule']
        #         else:
        #             raise Exception("No molecule POST'ed to resource")
        #     else:
        #         molecule = request.data.decode("utf-8")
        # try:
        #     # If the molecule string is base64 encoded
        #     if args['base64']:
        #         molecule = util.decode_string(molecule)
        #     # Read the molecule
        #     mol = OEGraphMol()
        #     OEReadMolFromBytes(mol, OEGetFileType(args['molfmt']), bool(args['gzip']), molecule)
        #     # unpack highlight-atoms-JSON data into paired lists (so data has same format as GET request)
        #     json_data = args['highlight-atoms-JSON']
        #     args['highlight-atoms'], args['highlight-atoms-colors'] = [], []
        #     for i, val in enumerate(json_data):
        #         atom_set = val.get('atom-indices', None)
        #         if atom_set:
        #             atom_set = util.normalize_atom_indices(atom_set, args['index-start'])
        #             color = val.get('color', None)
        #             args['highlight-atoms'].append(atom_set)
        #             args['highlight-atoms-colors'].append(color)
        #
        #     # Render the image
        #     return self.__render_image(mol, args)
        # # On error render a PNG with an error message
        # except Exception as ex:
        #     if args['debug']:
        #         return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
        #     else:
        #         return util.render_error_image(args['width'], args['height'], str(ex))

    def __render_image(self, args):
        # Read the molecule from the moleucle string
        mol = OEGraphMol()
        # return Response(str(args), status=200, mimetype='text/plain')
        OEReadMolFromBytes(mol, OEGetFileType(args['molfmt']), args['gzip'], args['molecule'])
        if not mol.IsValid():
            if args['debug']:
                raise Exception("Invalid molecule -- format = {}, gzip = {}\n{}".format(
                    args['molfmt'], args['gzip'], args['molecule']))
            else:
                raise Exception("Invalid molecule")

        return Response(str(mol.NumAtoms()), status=200, mimetype='text/plain')

    # noinspection PyMethodMayBeStatic
    def __render_image_old(self, mol, args):
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
        size = args['size']                                            # Size, over-ridden by width and/or height
        width = args['width'] if args['width'] else size               # Image width
        height = args['height'] if args['height'] else size            # Image height
        title = args['title']                                          # Image title
        use_molecule_title = bool(args['keeptitle'])                   # Use the molecule title in the molecule file
        bond_scaling = bool(args['scalebonds'])                        # Bond width scales with size
        image_format = args['imgfmt']                                  # The output image format
        image_mimetype = util.get_image_mime_type(image_format)        # MIME type corresponding to the image format
        title_location = util.get_title_location(args['titleloc'])     # The title location (if we have a title)
        background = util.get_color_from_rgba(args['background'])      # Background color
        highlight_ss = args['highlight-ss']                            # SMARTS substructures to highlight
        oe_highlight = util.get_oe_highlighting(args['highlight-style']) # The OE highlighting class
        highlight_style = args['highlight-style']                      # The substructure highlighting style (str)
        color_gen = util.get_color_generator(args['highlight-color'])  # Highlight color generator
        highlight_atoms = args['highlight-atoms']                      # List of atom index lists to highlight
        highlight_atoms_colors = args['highlight-atoms-colors']        # Optional paired list of colors for atom list
        nest = args['highlight-nest']                                  # Whether to nest overlapped highlights (bool)
        atom_labels = dict(args['atom-labels'])                        # Atom labels as {1: "label  1", 2: "label 2"}
        bond_labels = dict(args['bond-labels'])                        # Bond labels (same as atom labels)
        label_color = util.get_color_from_rgba(args['label-color'])    # Label Coloring
        label_style = util.get_font_style(args['label-style'])         # Label Style
        index_start = args['index-start']
        highlight_scale = args['highlight-scale']                      # scale of highlighting relative to default

        # Make sure we got valid inputs
        if not image_mimetype:
            raise Exception("Invalid MIME type")

        # Defaults for invalid inputs
        if not highlight_style:
            highlight_style = 'default'

        if not title_location:
            title_location = OETitleLocation_Top

        # if highlighting by cogwheel, can't use transparent background
        if highlight_atoms or highlight_ss and oe_highlight == OEHighlightByCogwheel:
            background.SetA(255)
        # *********************************************************************
        # *                      Create the Image                             *
        # *********************************************************************
        image = OEImage(width, height)
        # Prepare the depiction and set some prettier label defaults
        OEPrepareDepiction(mol, False, True)
        opts = OE2DMolDisplayOptions(image.GetWidth(), image.GetHeight(), OEScale_AutoScale)
        opts.SetAtomLabelFontScale(1.4)
        opts.SetAtomPropLabelFontScale(1.4)
        opts.SetBondPropLabelFontScale(1.4)
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

        # Do atom labels
        atomlabel = ApplyAtomLabels(atom_labels, index_start)
        opts.SetAtomPropertyFunctor(atomlabel)

        # Do bond labels
        bondlabel = ApplyBondLabels(bond_labels, index_start)
        opts.SetBondPropertyFunctor(bondlabel)

        # Set color of atom and bond labels
        font = OEFont()
        font.SetStyle(label_style)
        font.SetColor(label_color)
        opts.SetAtomPropLabelFont(font)
        opts.SetBondPropLabelFont(font)

        # Prepare the display
        disp = OE2DMolDisplay(mol, opts)

        # *********************************************************************
        # *           Set up Highlighting by SS or Atom Indices               *
        # *********************************************************************

        # List of dicts of atom sets we intend to highlight:
        # {'OEMapping': OEMatch or OEAtomBondSet, 'color': oe_color, 'atom_indices': atom_indices, 'scale': int}
        highlight_set_list = []

        # Build substructure mapping sets
        if highlight_ss:
            highlight_set_list += util.build_highlight_set_from_ss(mol, highlight_ss, color_gen, highlight_scale)

        # Build atom-based highlighting mapping sets
        if highlight_atoms:
            for i, atom_set in enumerate(highlight_atoms):
                # if atom set has a color, use it otherwise fall back to highlight-color preference
                if i >= len(highlight_atoms_colors) or not highlight_atoms_colors[i]:
                    oe_color = next(color_gen)
                else:
                    oe_color = util.get_color_from_rgba(highlight_atoms_colors[i])
                # convert atom indices to OEAtomBond set, add highlight_color attrib, and append to list
                oe_ab_set =util.get_OEAtomBondSet_from_indices(mol, atom_set)
                highlight_set_list.append({'OEMapping': oe_ab_set,
                                           'color': oe_color,
                                           'atom_indices': set(atom_set),
                                           'scale': highlight_scale})

        # *** Do Un-nested Highlighting ***
        if not nest or oe_highlight == OEHighlightByColor:    # we can't nest highlighting by color

            # apply_highlighting(disp, highlight_set_list, highlight_scale)

            oe_hl = util.get_scaled_highlighting(highlight_style)
            for hl_set in highlight_set_list:
                highlight = oe_hl.highlight(hl_set['color'], hl_set['scale'])
                OEAddHighlighting(disp, highlight, hl_set['OEMapping'])

        # *** Do Nested Highlighting ***
        else:
            # get atom indices
            for hl_set in highlight_set_list:
                hl_set['atom_indices'] = util.get_atom_indices(hl_set['OEMapping'])

            # sort highlight groups by number of highlighted atoms
            highlight_set_list = sorted(highlight_set_list, key=lambda t: len(t['atom_indices']), reverse=False)

            # iterate over groups, starting at shorter atom sets.  Count up the number of times each atom
            # is highlighted, and use the max value of those atoms to set the relative size of each highlighting group
            atom_idx_cnts = {}
            for hl_set in highlight_set_list:
                highlight_counts = []
                for idx in hl_set['atom_indices']:
                    # tally number of times each atom is highlighted
                    if idx not in atom_idx_cnts:
                        atom_idx_cnts[idx] = 1
                    else:
                        atom_idx_cnts[idx] += 1
                    highlight_counts.append(atom_idx_cnts[idx])

                # set relative size to the maximum number of highlights within this set
                # if only one highlight, subtract 1 so we start at 0
                # minimum size is whatever highlight_scale is
                hl_set['scale'] = max(highlight_counts) - 1 + highlight_scale

            # sort by size descending
            highlight_set_list = sorted(highlight_set_list, key=lambda t: t['scale'], reverse=True)
            oe_hl = util.get_scaled_highlighting(highlight_style)
            for hl_set in highlight_set_list:
                highlight = oe_hl.highlight(hl_set['color'], hl_set['scale'])
                OEAddHighlighting(disp, highlight, hl_set['OEMapping'])

        # *********************************************************************
        # *                    Render and return the image                    *
        # *********************************************************************
        OERenderMolecule(image, disp)

        # Return the image in the response
        img_content = OEWriteImageToString(image_format, image)
        return Response(img_content, mimetype=image_mimetype)
