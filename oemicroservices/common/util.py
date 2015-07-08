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

import base64
import zlib

from openeye.oechem import *
from openeye.oedepict import *

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

# Dictionary of OpenEye title locations
__title_locations = {
    'top': OETitleLocation_Top,
    'bottom': OETitleLocation_Bottom
}

# Substructure highlight styles
__highlight_styles = {
    'default': OEHighlightStyle_Default,
    'ballandstick': OEHighlightStyle_BallAndStick,
    'stick': OEHighlightStyle_Stick,
    'color': OEHighlightStyle_Color,
    'cogwheel': OEHighlightStyle_Cogwheel
}

########################################################################################################################
#                                                                                                                      #
#                                               Utility Functions                                                      #
#                                                                                                                      #
########################################################################################################################

def get_color_from_rgba(rgba):
    """
    Get an OpenEye color from an RRGGBBAA string
    :param rgba: The RRGGBBAA hex string
    :return: An OEColor object corresponding to the RGBA color
    """
    rgba = rgba.replace('#', '')
    # Check if we have valid hex
    try:
        int(rgba, 16)
    except ValueError:
        raise ValueError("Invalid RGBA string: {0}".format(rgba))
    return OEColor("#{0}".format(rgba))


def get_title_location(location):
    """
    Returns an OETitleLocation or None if the title location is not recognized
    :param location: The text title location (top | bottom)
    :return: The corresponding OETitleLocation or None if location is not a valid OETitleLocation
    """
    return __title_locations.get(location.lower())


def get_image_mime_type(ext):
    """
    Returns an image MIME type from common image extensions
    :param ext: The image extension
    :return: The image MIME type or None if the image extension is not known
    """
    return __mime_types.get(ext.replace('.', '').lower())


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
    Gzip and then b64 encode a string
    :param s: The string to encode
    :type s: str
    :return: The b64 encoded gzipped string
    :rtype: str
    """
    return base64.b64encode(compress(s.encode("utf-8"))).decode("utf-8")


def inflate_string(s):
    """
    Inflate a gzipped and b64 encoded string
    :param s: The string to inflate
    :type s: str
    :return: The inflated string
    :rtype: str
    """
    return zlib.decompress(base64.b64decode(s.encode('utf-8')), zlib.MAX_WBITS | 16).decode('utf-8')


def read_molecule_from_string(mol_string, extension, gz=False, reparse=False):
        """
        Read a molecule from a molecule string
        :param mol_string: The molecule represented as a string
        :type mol_string: str
        :param extension: The file extension indicating the file format of mol_string
        :type extension: str
        :param gz: Whether mol_string is a base64-encoded gzip
        :type gz: bool
        :param reparse: Whether we should reparse connectivity, bond orders, stereo, etc.,
        :type reparse: bool
        :return: The OEGraphMol representation of the molecule
        :rtype: OEGraphMol
        """
        mol = OEGraphMol()
        # Create the molecule input stream
        ifs = oemolistream()

        # Get the molecule format
        if extension.lower() == "smiles":
            mol_format = OEFormat_SMI
        else:
            mol_format = OEGetFileType(extension)
        if mol_format == OEFormat_UNDEFINED:
            raise Exception("Invalid molecule format: " + extension)

        ifs.SetFormat(mol_format)

        # Open stream to the molecule string
        if gz:
            ok = ifs.openstring(inflate_string(mol_string))
        else:
            ok = ifs.openstring(mol_string)

        # If opening the molecule string was not OK
        if not ok:
            raise Exception("Error opening molecule")

        # If we opened the stream then read the molecule
        ok = OEReadMolecule(ifs, mol)

        # If reading the molecule was not OK
        if not ok:
            raise Exception("Invalid molecule")

        # If we are reparsing the molecule
        if reparse:
            OEDetermineConnectivity(mol)
            OEFindRingAtomsAndBonds(mol)
            OEPerceiveBondOrders(mol)
            OEAssignImplicitHydrogens(mol)
            OEAssignFormalCharges(mol)
        return mol
