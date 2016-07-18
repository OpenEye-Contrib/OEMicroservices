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

from flask import Response

import zlib
import base64
# noinspection PyUnresolvedReferences
import sys
import mimetypes

from openeye.oechem import *
from openeye.oedepict import *

from werkzeug.datastructures import MultiDict, CombinedMultiDict

# Initialize known mimetypes
mimetypes.init()

############################
# Python 2/3 Compatibility #
############################

try:
    from gzip import compress
except ImportError:
    # Compress for Python 2.x
    def compress(s):
        # Imports just for this function
        import StringIO
        import gzip
        # Write the compressed string
        sio = StringIO.StringIO()
        with gzip.GzipFile(fileobj=sio, mode='w') as gz:
            gz.write(s)
        gz.close()
        return sio.getvalue()

# To support unicode as UTF-8 in Python 2 and 3
if sys.version_info < (3,):
    def to_utf8(u):
        return u.encode('utf-8')
else:
    def to_utf8(u):
        return u

########################################################################################################################
#                                                                                                                      #
#                                                 CONSTANTS                                                            #
#                                                                                                                      #
########################################################################################################################

DEFAULT_HIGHLIGHT_MIN_WIDTH = 2

########################################################################################################################
#                                                                                                                      #
#                                             CONSTANT DICTIONARIES                                                    #
#                                                                                                                      #
# The following dictionaries are used to translate supported file formats, etc. Feel free to add more to these. They   #
# are meant to only be used within the utility functions exposed by this module.                                       #
#                                                                                                                      #
########################################################################################################################

# Dictionary of supported image MIME types
__mime_types = {
    'svg': 'image/svg+xml',
    'png': 'image/png',
    'pdf': 'application/pdf',
    'ps': 'application/postscript'
}

# Substructure highlight styles
__highlight_styles = {
    'default': OEHighlightStyle_Default,
    'ballandstick': OEHighlightStyle_BallAndStick,
    'stick': OEHighlightStyle_Stick,
    'color': OEHighlightStyle_Color,
    'cogwheel': OEHighlightStyle_Cogwheel
}

# Highlighting classes for atom and substructure styles
__highlight_classes = {
    'default': OEHighlightByStick,
    'ballandstick': OEHighlightByBallAndStick,
    'stick': OEHighlightByStick,
    'color': OEHighlightByColor,
    'cogwheel': OEHighlightByCogwheel,
    'lasso': OEHighlightByLasso
}

# Highlighting defaults for atom and substructure styles
__highlight_default_settings = {
    OEHighlightByBallAndStick: {"stickWidthScale": 3.0, "ballRadiusScale": 3.0, "monochrome": True},
    OEHighlightByStick: {"stickWidthScale": 3.0, "monochrome": True, "atomExternalHighlightRatio": 0.0},
    OEHighlightByColor: {"lineWidthScale": 1.5},
    OEHighlightByCogwheel: {"lineWidthScale": 1.5, "stickWidthScale": 2.0, "ballRadiusScale": 2.0,
                            "innerContour": False, "monochrome": False},
    OEHighlightByLasso: {"lassoScale": 3.0, "monochrome": False}
}

# Default highlighting widths by highlighting style
__highlight_default_widths = {
    'default': 0.5,
    'ballandstick': 3,
    'stick': 3,
    'color': 1.5,
    'cogwheel': 1.5
}

# Default highlighting color palettes
__highlight_colors = {
    'default': OEGetLightColors,
    'contrast': OEGetContrastColors,
    'deep': OEGetDeepColors,
    'light': OEGetLightColors,
    'vivid': OEGetVividColors
}

# Available font styles
__font_styles = {
    'default': OEFontStyle_Normal,
    'bold': OEFontStyle_Bold,
    'italic': OEFontStyle_Italic,
    'normal': OEFontStyle_Normal
}

########################################################################################################################
#                                                                                                                      #
#                                               Utility Functions                                                      #
#                                                                                                                      #
########################################################################################################################

def get_highlight_style(style):
    """
    Returns an OEHighlightStyle corresponding to a text style name
    :param style: The text style name
    :type style: str
    :return: The OEHighlightStyle or None if the style name is not known
    """
    return __highlight_styles.get(style.lower())


def render_error_image(width, height, message="Error depicting molecule"):
    """
    Render an image with error text
    :param width: The image width
    :type width: int or float
    :param height: The image height
    :type height: int or float
    :param message: The error text to put on the image (WARNING: does not wrap)
    :type message: str
    :return: An HTTP response with the error image
    """
    image = OEImage(width, height)
    font = OEFont(OEFontFamily_Helvetica, OEFontStyle_Default, 20, OEAlignment_Center, OERed)
    image.DrawText(OE2DPoint(image.GetWidth()/2.0, image.GetHeight()/2.0), message, font, image.GetWidth())
    # Render the image
    img_content = OEWriteImageToString('png', image)
    return Response(img_content, mimetype='image/png')


def compress_string(s):
    """
    Compress a string using gzip
    :param s: The string to compress
    :type s: str
    :return: The gzipped string
    :rtype: bytearray
    """
    return compress(s.encode("utf-8"))


def inflate_string(s):
    """
    Inflate a gzipped string
    :param s: The string to inflate
    :type s: str
    :return: The inflated string
    :rtype: str
    """
    return zlib.decompress(s, zlib.MAX_WBITS | 16)

########################################################################################################################
#                                                                                                                      #
#                                         Utility Functions for v2 of API                                              #
#                                                                                                                      #
########################################################################################################################


def get_font_style(style):
    """
    :param style: The text font style (default | normal |
    :return: The corresponding OEFontStyle
    """
    return __font_styles.get(style.lower(), 'default')


def get_oe_highlighting(style):
    """
    Returns an OEHighlightStyle corresponding to a text style name
    :param style: The text style name
    :type style: str
    :return: The OEHighlightStyle or None if the style name is not known
    """
    return __highlight_classes.get(style.lower())


def get_highlight_width(style, highlight_min_width):
    """
    Sets default minimum width using style to intelligently pick
    :param style: string describing style
    :type: str
    :param highlight_min_width:
    :type: number
    :return: number
    """
    if highlight_min_width:
        return highlight_min_width
    elif style.lower() in ["color", "ballandstick"]:
        return 1
    else:
        return DEFAULT_HIGHLIGHT_MIN_WIDTH


def normalize_atom_indices(indices, start=0):
    """
    Ensures atom indices are integers and normalize to starting point
    :param atom_indices: list of indices
    :type: iterable of strings or ints that can be coerced into int
    :param indices: Array of atom indices
    :param start: Atom index start point (0 most common, 1 if from Pipeline Pilot)
    :type: int
    :return: normalized indices
    :type: int list
    """
    return [int(idx) - start for idx in indices]


def fix_highlight_atoms_from_get(list_of_csv_indices, index_start=0):
    """
    Converts lists like ['1,2,3','4,5,6'] to [[1,2,3],[4,5,6]] and normalizes integers to a start point
    :param list_of_csv_indices: list in format ['1,2,3','4,5,6']
    :param index_start: starting point for atom numbering, default 0
    :return: list of normalized integer lists
    """
    return [normalize_atom_indices(sublist.split(','), index_start) for sublist in list_of_csv_indices]


def get_OEAtomBondSet_from_indices(molecule, atom_indices, include_bonds=True, **kwargs):
    """
    :param molecule: An OEGraphMol object
    :param atom_indices: An iterable containing atom index integers
    :param include_bonds: Whether or not to include interconnecting bonds
    :param kwargs: all additional keyword arguments are added as attributes to the OEAtomBondSet
    :return: an OEAtomBondSet with atoms and their connecting bonds
    """
    ab_set = OEAtomBondSet()
    allBonds = set()
    for idx in atom_indices:
        atom = molecule.GetAtom(OEHasAtomIdx(idx))
        ab_set.AddAtom(atom)
        if include_bonds:
            for bond in atom.GetBonds():
                if bond in allBonds:        # if we've seen this bond before, it links two atoms so add it
                    ab_set.AddBond(bond)
                else:
                    allBonds.add(bond)      # if we haven't seen it, add it to the tracking set

    for key, val in kwargs.items():         # assign kwargs as attributes on OEAtomBondSet
        setattr(ab_set, key, val)

    return ab_set


def get_color_generator(colorset='default'):
    """
    Returns and unending supply of colors, given a specific color in hex (e.g. #FFFFFF, a list of colors in hex, or
    a string describing one of the default OE color sets (contrast, deep, light, vivid)
    :param color: string describing default color palette, a color in hex, or a list of colors in hex
    :type: str or list
    :return: an infinite generator that always OE Colors
    :type: generator
    """

    # if a hex color, always return that hex color converted to OEColor
    if isinstance(colorset, str) and colorset.startswith('#'):
        colorset = [colorset]

    # if a list of hex colors, always return that list converted to OEColors, loop if we reach the end of the list
    if isinstance(colorset, list):

        def user_color_generator(color_list):
            while True:
                for color in color_list:
                    yield get_color_from_rgba(color)

        gen = user_color_generator(colorset)

    # if no valid colors given, choose one of the default highlight colors sets
    else:

        def oe_colorset_generator(oe_colors_iter):
            while True:
                for oecolor in oe_colors_iter():
                    yield oecolor

        oe_colorset = __highlight_colors.get(colorset.lower(), __highlight_colors['default'])
        gen = oe_colorset_generator(oe_colorset)

    return gen


def get_atom_indices(match_or_abset):
    """
    Accepts an OEMatch or OEAtomBondSet and returns set of atom indices
    :param match_or_abset: An OEMatch or OEAbset
    :return: set of atom indices
    """
    atoms = match_or_abset.GetAtoms()
    atom_indices = set()
    # we have to pull atoms out differently for OEMatches and OEAtomBondSets
    for atom in atoms:
        if hasattr(atom, 'target'):         # OEMatch
            atom_indices.add(atom.target.GetIdx())
        else:                               # OEAtomBondSet
            atom_indices.add(atom.GetIdx())

    return atom_indices


def build_highlight_set_from_ss(oe_mol, highlight_ss, color_generator, highlight_scale):
    """
    :param OEmol: An OEMol object
    :param highlight_ss: A substructure query as SMILES
    :param color_generator: Color generator from get_color_generator()
    :param highlight_scale: Scale multiplier for highlighting. Will get overridden in nested highlighting
    :return: A list of atom highlighting dicts as used by do_highlighting function in format:
             {'OEMapping': OEMatch or OEAtomBondSet, 'color': oe_color, 'atom_indices': atom_indices, 'scale': int}
    """
    highlight_set_list = []
    for querySmiles in highlight_ss:
        subs = OESubSearch(querySmiles)
        for match in subs.Match(oe_mol, True):
            oe_color = next(color_generator)
            atom_indices = get_atom_indices(match)
            highlight_set_list.append({'OEMapping': match,
                                       'color': oe_color,
                                       'atom_indices': atom_indices,
                                       'scale': highlight_scale})
    return highlight_set_list


########################################################################################################################
#                                                                                                                      #
#                           Helper Classes and Factory for doing scaled highlighting                                   #
#                                                                                                                      #
########################################################################################################################

class ScaledHighlighting():
    """
    Class for scaling a value by a preset scale multiplier
    """
    def __init__(self, scaleMultiplier=1.5):
        """
        :param scaleMultiplier:  The predefined scale multiplier we'll use
        """
        self.scaleMultiplier = scaleMultiplier

    def _scale(self, scale, value):
        """
        Returns a value + it's scaleMultiplier * it's scale
        :param scale: the scale by which we're scaling the multiplier (typically an integer counter)
        :param value: the value to which we're adding the scaled multiplier
        :return:
        """
        return value + self.scaleMultiplier * scale


class CogwheelHighlighting(ScaledHighlighting):
    """
    Class for doing scaled cogwheel highlighting
    """
    def __init__(self, scaleMultiplier=2.1, lineWidthScale=1.5, stickWidthScale=2.0, ballRadiusScale=2.0,
                 innerContour=False, monochrome=True):
        """
        Sets initial parameters for OEHighlightByCogwheel
        :param scaleMultiplier: For each scaling factor, the scale by which we'll increase
        :param lineWidthScale: OEHighlightByCogwheel arg (does not scale)
        :param stickWidthScale: OEHighlightByCogwheel arg (scales)
        :param ballRadiusScale: OEHighlightByCogwheel arg (scales)
        :param innerContour: OEHighlightByCogwheel arg
        :param monochrome: OEHighlightByCogwheel arg
        :return:
        """
        ScaledHighlighting.__init__(self, scaleMultiplier)
        self.lineWidthScale = lineWidthScale
        self.stickWidthScale = stickWidthScale
        self.ballRadiusScale = ballRadiusScale
        self.innerContour = innerContour
        self.monochrome = monochrome

    def highlight(self, color, scale):
        # Do scaling
        return OEHighlightByCogwheel(color, self.lineWidthScale, self._scale(scale, self.stickWidthScale),
                              self._scale(scale, self.ballRadiusScale), self.innerContour, self.monochrome)


class BallAndStickHighlighting(ScaledHighlighting):
    """
    Class for doing scaled Ball and Stick Highlighting
    """
    def __init__(self, scaleMultiplier=1.5, stickWidthScale=3, ballRadiusScale=3, monochrome=True):
        """
        Sets initial parameters for OEHighlightByBallAndStick
        :param scaleMultiplier: For each scaling factor, the scale by which we'll increase
        :param stickWidthScale: OEHighlightByBallAndStick arg (scales)
        :param ballRadiusScale: OEHighlightByBallAndStick arg (scales)
        :param innerContour: OEHighlightByBallAndStick arg
        :param monochrome: OEHighlightByBallAndStick arg
        :return:
        """
        ScaledHighlighting.__init__(self, scaleMultiplier)
        self.stickWidthScale = stickWidthScale
        self.ballRadiusScale = ballRadiusScale
        self.monochrome = monochrome

    def highlight(self, color, scale):
        return OEHighlightByBallAndStick(color, self._scale(scale, self.stickWidthScale),
                                  self._scale(scale, self.ballRadiusScale), self.monochrome)


class StickHighlighting(ScaledHighlighting):
    """
    Class for doing scaled Stick Highlighting
    """
    def __init__(self, scaleMultiplier=3.5, stickWidthScale=4, monochrome=True, atomExternalHighlightRatio=0.0):
        """
        Sets initial parameters for OEHighlightByStick
        :param scaleMultiplier: For each scaling factor, the scale by which we'll increase
        :param stickWidthScale: OEHighlightByStick arg (scales)
        :param monochrome: OEHighlightByStick arg
        :param atomExternalHighlightRatio: OEHighlightByStick arg (does not scale)
        :return:
        """
        ScaledHighlighting.__init__(self, scaleMultiplier)
        self.stickWidthScale = stickWidthScale
        self.monochrome = monochrome
        self.atomExternalHighlightRatio = atomExternalHighlightRatio

    def highlight(self, color, scale):
        return OEHighlightByStick(color, self._scale(scale, self.stickWidthScale), self.monochrome,
                           self.atomExternalHighlightRatio)


class LassoHighlighting(ScaledHighlighting):
    """
    Class for doing Lasso Highlighting
    """
    def __init__(self, scaleMultiplier=2, lassoScale=3):
        """
        Sets initial parameters for OEHighlightByLasso
        :param scaleMultiplier: For each scaling factor, the scale by which we'll increase
        :param lassoScale: OEHighlightByLasso arg (scales)
        :return:
        """
        ScaledHighlighting.__init__(self,scaleMultiplier)
        self.lassoScale = lassoScale

    def highlight(self, color, scale):
        return OEHighlightByLasso(color, self._scale(scale, self.lassoScale))


class ColorHighlighting():
    """
    Class for doing color highlighting
    """
    def __init__(self, lineWidthScale=1):
        """
        :param lineWidthScale: OEHighlightByColor arg
        :return:
        """
        self.lineWidthScale = lineWidthScale

    #
    def highlight(self, color, scale=0):
        return OEHighlightByColor(color, self.lineWidthScale)


def get_scaled_highlighting(highlight_style, **kwargs):
    """
    Factory for returning a scaled highlighting class.  Returned class uses logical defaults for scaling nested
    highlighting on the structure, including a scaleMultiplier parameter which adjusts the size of the highlighting
    through a scale of 0-n integers
    :param highlight_style:
    :param kwargs: scaleMultiplier for scaled highlighting classes (everything but color) and initial settings for
                   highlighting for the wrapped OEHighlightClass
    :return: the scalable highlighting class.  To use the returned class, call its highlight method
    """
    __classes = {'default':      CogwheelHighlighting,
                 'cogwheel':     CogwheelHighlighting,
                 'stick':        StickHighlighting,
                 'lasso':        LassoHighlighting,
                 'ballandstick': BallAndStickHighlighting,
                 'color':        ColorHighlighting}

    hl_class = __classes.get(highlight_style.lower(), CogwheelHighlighting)  #default to cogwheel
    return hl_class(**kwargs)


def stringify_error_dict(d):
    return "\n".join(["{}: {}".format(p, e if not type(e) == type(list()) else "; ".join(e)) for p, e in d.items()])

def make_response_from_error_dict(d):
    """
    Create a response from an error dictionary
    :param d: A dictionary of errors (will be formatted key: value on each line
    :return: A Flask Response with the errors as the body
    """
    error = stringify_error_dict(d)
    return Response(error, status=400, mimetype='text/plain')

def get_mimetype(ext):
    """
    Safe get MIMETYPE from file extension
    :param ext: The file extension
    :return: The corresponding MIMETYPE or None if unknown
    """
    if not ext:
        return None
    try:
        if ext[0] == '.':
            return mimetypes.types_map[ext]
        else:
            return mimetypes.types_map[".{}".format(ext)]
    # If the type is not found
    except KeyError:
        return None

def combine_query_and_json_parameters(request):
    """
    Combine query arguments with parameters posed from JSON. This will also take any repeated parameter and create an
    array, whereas non-repeated parameters will be single objects.
    NOTE: This is modeled after the implementation of request.values in werkzeug.wrappers
    :param request: The incoming request
    :return: A CombinedMultiDict with the
    """
    # TODO: Handle array objects
    args = []
    # Handle the query parameters
    if not isinstance(request.args, MultiDict):
        args.append(MultiDict(request.args))
    else:
        args.append(request.args)
    # Handle the JSON parameters
    if request.is_json:
        j = request.get_json()
        if not isinstance(j, MultiDict):
            args.append(MultiDict(j))
        else:
            args.append(j)
    cm = CombinedMultiDict(args)
    # Create a final dictionary (processed) that will hold arrays of input arguments only if multiple input arguments
    # were given, otherwise it holds the single argument -- this is the schema processed and validated by Marshmallow
    processed = {}
    for key in cm.keys():
        val = cm.getlist(key)
        # Sanity check: do not keep empty keys
        if not val:
            continue
        # Keep arrays only if the key has multiple values
        if len(val) > 1:
            processed[key] = val
        # Otherwise take the only value in the array
        else:
            processed[key] = val.pop()
    return processed