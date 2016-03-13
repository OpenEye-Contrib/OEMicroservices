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
# from openeye.oechem import *

from openeye.oedepict import *

from oemicroservices.common.functor import (
    ApplyAtomLabelsFunctor,
    ApplyBondLabelsFunctor)

from oemicroservices.resources.depict.base import depictor_base_arg_parser_v2
from oemicroservices.common.util import (
    render_error_image,
    get_image_mime_type,
    get_color_from_rgba,
    get_title_location,
    get_image_width_and_height,
    read_molecule_from_string,
    get_oe_highlighting,
    fix_highlight_atoms_from_get,
    get_color_generator,
    get_font_style,
    get_scaled_highlighting,
    get_OEAtomBondSet_from_indices,
    build_highlight_set_from_ss,
    normalize_atom_indices,
    get_atom_indices)

########################################################################################################################
#                                                                                                                      #
#                                        Molecule depictor argument parser                                             #
#                                                                                                                      #
########################################################################################################################

# Extend the standard image_parser
depictor_arg_parser = depictor_base_arg_parser_v2.copy()
# Only for POST: the molecule string
depictor_arg_parser.add_argument('molecule', type=str, default='')
# The format of the molecule string
depictor_arg_parser.add_argument('molecule-format', type=str, default='smiles')
# The image size (assuming a square image)
depictor_arg_parser.add_argument('size', type=int, default=400)
# The image width - uses size by default in parsing logic below.  If defined, overrides size.
depictor_arg_parser.add_argument('width', type=int)
# The image height - uses size by default in parsing logic below.  If defined, overrides size.
depictor_arg_parser.add_argument('height', type=int)
# Substructure to highlight (multiple values allowed)
depictor_arg_parser.add_argument('highlight-ss', type=str, action='append')
# Hex code or string for coloring the substructure
depictor_arg_parser.add_argument('highlight-color',  type=str, default='default')
# Style in which to render the highlighted substructure (color, stick, ballandstick, cogwheel)
depictor_arg_parser.add_argument('highlight-style',  type=str, default='default')
# For stick, ballandstick, and cogwheel styles, should we "nest" highlighting or keep all the same width
depictor_arg_parser.add_argument('highlight-nest',  type=bool, default=True)
# Scale by which highlighting can be modified.  0 is default, count up with integers.
depictor_arg_parser.add_argument('highlight-scale', type=int, default=0)
# For highlighting atoms by number: whether atoms indices count up by 1 or 0.  Atom numbers start at 0 using OEMol
# numbering, set to 1 if calling from Pipeline Pilot
depictor_arg_parser.add_argument('index-start', type=int, default=0)

# Optional GET arguments for doing atom highlighting by color and atom number
# Comma separated list of atom numbers - we'll convert to int array inside the get method
# These arrays should be of matched length, each atom set will correspond to the color of the matching index.
# If the matching index in highlightatomscolor isn't there, the color defaults to the highlight color argument.
depictor_arg_parser.add_argument('highlight-atoms', type=str, action='append', default=[])
# Atom coloring, index in this array should match index in highlight-atoms
depictor_arg_parser.add_argument('highlight-atoms-colors', type=str, action='append', default=[])

# Optional POST arguments for doing atom highlighting by color and atom number
# JSON should be a list of dicts (or array of objects) in the following format
# [{ "atom-indices": [1,2,3], "color": "#0123FF" }, ...]
# Color is optional, but atom-indices is required
depictor_arg_parser.add_argument('highlight-atoms-JSON', type=list, location='json', default=[])

# POST-Only argument for adding atom labels.  Atom labels are specified as a lists of [atom index, label] diads
# e.g. [1, "label 1"], [14, "label 2"]
depictor_arg_parser.add_argument('atom-labels', type=list, location='json', default=[])
# POST-Only argument for adding bond labels.  Atom labels are specified as a lists of [bond index, label] diads
depictor_arg_parser.add_argument('bond-labels', type=list, location='json', default=[])
# Color of atom/bondlabels
depictor_arg_parser.add_argument('label-color', type=str, default='#404040')
# Style of atom/bond labels
depictor_arg_parser.add_argument('label-style', type=str, default='default')


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
        # Parse the query options
        args = depictor_arg_parser.parse_args()

        # return Response(json.dumps(args), status=400, mimetype='application/json')
        try:
            # Read the molecule
            mol = read_molecule_from_string(molecule, args['molecule-format'], bool(args['gz']), bool(args['reparse']))
            # fix highlight-atoms sets coming from URL (comma-separated values to int list)
            args['highlight-atoms'] = fix_highlight_atoms_from_get(args['highlight-atoms'], args['index-start'])
            # Render the image
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                width, height = get_image_width_and_height(args)
                return render_error_image(width, height, str(ex))

    def post(self, molecule=''):
        """
        Render an image with the molecule POST'ed to this resource
        :param molecule: The molecule string to be rendered
        :return: The rendered image
        :rtype: Response
        """
        # Parse the query options
        args = depictor_arg_parser.parse_args()
        # if body is json, extract molecule from molecule field, otherwise assume that the body contains the molecule
        if not molecule:
            if request.mimetype == 'application/json':
                molecule = args['molecule']
            else:
                molecule = request.data.decode("utf-8")

        try:
            # Read the molecule
            mol = read_molecule_from_string(molecule, args['molecule-format'], bool(args['gz']), bool(args['reparse']))

            # unpack highlight-atoms-JSON data into paired lists (so data has same format as GET request)
            json_data = args['highlight-atoms-JSON']
            args['highlight-atoms'], args['highlight-atoms-colors'] = [], []
            for i, val in enumerate(json_data):
                atom_set = val.get('atom-indices', None)
                if atom_set:
                    atom_set = normalize_atom_indices(atom_set, args['index-start'])
                    color = val.get('color', None)
                    args['highlight-atoms'].append(atom_set)
                    args['highlight-atoms-colors'].append(color)

            # Render the image
            return self.__render_image(mol, args)
        # On error render a PNG with an error message
        except Exception as ex:
            if args['debug']:
                return Response(json.dumps({"error": str(ex)}), status=400, mimetype='application/json')
            else:
                width, height = get_image_width_and_height(args)
                return render_error_image(width, height, str(ex))

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
        size = args['size']                                            # Size, over-ridden by width and/or height
        width = args['width'] if args['width'] else size               # Image width
        height = args['height'] if args['height'] else size            # Image height
        title = args['title']                                          # Image title
        use_molecule_title = bool(args['keep-title'])                  # Use the molecule title in the molecule file
        bond_scaling = bool(args['scale-bonds'])                       # Bond width scales with size
        image_format = args['image-format']                            # The output image format
        image_mimetype = get_image_mime_type(image_format)             # MIME type corresponding to the image format
        title_location = get_title_location(args['titleloc'])          # The title location (if we have a title)
        background = get_color_from_rgba(args['background'])           # Background color
        highlight_ss = args['highlight-ss']                            # SMARTS substructures to highlight
        oe_highlight = get_oe_highlighting(args['highlight-style'])    # The OE highlighting class
        highlight_style = args['highlight-style']                      # The substructure highlighting style (str)
        color_gen = get_color_generator(args['highlight-color'])       # Highlight color generator
        highlight_atoms = args['highlight-atoms']                      # List of atom index lists to highlight
        highlight_atoms_colors = args['highlight-atoms-colors']        # Optional paired list of colors for atom list
        nest = args['highlight-nest']                                  # Whether to nest overlapped highlights (bool)
        atom_labels = dict(args['atom-labels'])                        # Atom labels as {1: "label  1", 2: "label 2"}
        bond_labels = dict(args['bond-labels'])                        # Bond labels (same as atom labels)
        label_color = get_color_from_rgba(args['label-color'])         # Label Coloring
        label_style = get_font_style(args['label-style'])              # Label Style
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
        atomlabel = ApplyAtomLabelsFunctor(atom_labels, index_start)
        opts.SetAtomPropertyFunctor(atomlabel)

        # Do bond labels
        bondlabel = ApplyBondLabelsFunctor(bond_labels, index_start)
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
            highlight_set_list += build_highlight_set_from_ss(mol, highlight_ss, color_gen, highlight_scale)

        # Build atom-based highlighting mapping sets
        if highlight_atoms:
            for i, atom_set in enumerate(highlight_atoms):
                # if atom set has a color, use it otherwise fall back to highlight-color preference
                if i >= len(highlight_atoms_colors) or not highlight_atoms_colors[i]:
                    oe_color = next(color_gen)
                else:
                    oe_color = get_color_from_rgba(highlight_atoms_colors[i])
                # convert atom indices to OEAtomBond set, add highlight_color attrib, and append to list
                oe_ab_set = get_OEAtomBondSet_from_indices(mol, atom_set)
                highlight_set_list.append({'OEMapping': oe_ab_set,
                                           'color': oe_color,
                                           'atom_indices': set(atom_set),
                                           'scale': highlight_scale})

        # *** Do Un-nested Highlighting ***
        if not nest or oe_highlight == OEHighlightByColor:    # we can't nest highlighting by color

            # apply_highlighting(disp, highlight_set_list, highlight_scale)

            oe_hl = get_scaled_highlighting(highlight_style)
            for hl_set in highlight_set_list:
                highlight = oe_hl.highlight(hl_set['color'], hl_set['scale'])
                OEAddHighlighting(disp, highlight, hl_set['OEMapping'])

        # *** Do Nested Highlighting ***
        else:
            # get atom indices
            for hl_set in highlight_set_list:
                hl_set['atom_indices'] = get_atom_indices(hl_set['OEMapping'])

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
            oe_hl = get_scaled_highlighting(highlight_style)
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