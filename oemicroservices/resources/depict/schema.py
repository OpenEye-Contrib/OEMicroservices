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

from marshmallow import Schema, fields, ValidationError, pre_load
from openeye.oedepict import *
from openeye.oechem import *

########################################################################################################################
#                                                                                                                      #
#                                            Base Image Depictions                                                     #
#                                                                                                                      #
########################################################################################################################


class TitleLocation(fields.Field):
    def _deserialize(self, value, attr, data):
        v = value.lower()
        if v == 'default':
            return OETitleLocation_Default
        if v == 'top':
            return OETitleLocation_Top
        elif v == 'bottom':
            return OETitleLocation_Bottom
        elif v == 'hidden':
            return OETitleLocation_Hidden
        else:
            raise ValidationError("Invalid title location: {}".format(value))


class ImageFormat(fields.Field):
    supported_formats = [ext.replace('.', '') for ext in OEGetSupportedImageFileExtensions()]

    def _validate(self, value):
        return value.lower().replace('.', '') in self.supported_formats

    def _deserialize(self, value, attr, data):
        return value.lower().replace('.', '')

    default_error_messages = {u'null': u'Field may not be null.', u'validator_failed': u'Invalid image format.',
                              u'required': u'Missing data for required field.', u'type': u'Invalid input type.'}


class Color(fields.Field):
    def _deserialize(self, value, attr, data):
        try:
            int(value, 16)
        except:
            raise ValidationError("Invalid RGBA value: {}".format(value))
        try:
            return OEColor("#{}".format(value))
        except Exception as ex:
            raise ValidationError("Error parsing color from {}: {}".format(value, str(ex)))


class FontStyle(fields.Field):
    def _deserialize(self, value, attr, data):
        v = value.lower()
        if v == 'default':
            return OEFontStyle_Normal,
        elif v == 'bold':
            return OEFontStyle_Bold,
        elif v == 'italic':
            return OEFontStyle_Italic,
        elif v == 'normal':
            return OEFontStyle_Normal
        else:
            raise ValidationError("Unknown font style: {}".format(v))


class BaseDepictorRequest(Schema):
    """
    The base schema for requesting an image depiction
    """
    keep_title = fields.Boolean(required=True, attribute='keep-title', missing=False)
    title = fields.String(required=False, missing="")
    gzip = fields.Boolean(required=False, missing=False)
    scale_bonds = fields.Boolean(required=False, missing=False)
    background = Color(required=False, missing="FFFFFF00")
    debug = fields.Boolean(required=False, missing=False)
    base64 = fields.Boolean(required=False, missing=False)
    size = fields.Integer(required=False)
    # Custom field types
    # The location of the title on the image
    title_loc = TitleLocation(required=False, attribute='title-loc', missing='default')
    # Image format: 'imgfmt' is API v2 and 'format' is API v1
    imgfmt = ImageFormat(required=True, missing='png')

########################################################################################################################
#                                                                                                                      #
#                                          Simple Molecule Depiction                                                   #
#                                                                                                                      #
########################################################################################################################


class HighlightStyle(fields.Field):
    def _deserialize(self, value, attr, data):
        v = value.lower()
        if v == 'default':
            return OEHighlightStyle_Default
        elif v == 'ballandstick':
            return OEHighlightStyle_BallAndStick
        elif v == 'stick':
            return OEHighlightStyle_Stick
        elif v == 'color':
            return OEHighlightStyle_Color
        elif v == 'lasso':
            return OEHighlightStyle_Lasso
        elif v == 'cogwheel':
            return OEHighlightStyle_Cogwheel
        else:
            raise ValidationError("Invalid highlight style: {}".format(value))


class TypedArray(fields.Field):
    """
    Implements an array of typed objects.
    """
    def __init__(self, *args, **kwargs):
        """
        Special parameters for this object:
        delimited = True/False  Whether the object will come in as a delimited string
        delimiter = ','  The delimiter to use to split the string
        type = str  The object to use to coercce the string
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        """
        self.delimited = False
        self.delimiter = ','
        self.type = str
        if 'delimited' in kwargs:
            self.delimited = kwargs.pop('delimited')
        if 'delimiter' in kwargs:
            self.delimiter = kwargs.pop('delimiter')
        if 'type' in kwargs:
            self.type = kwargs.pop('type')
        super(TypedArray, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        arr = []
        # If we get a list, then try to cast all the objects. We get a list here when flat=False is passed to to_dict
        if isinstance(value, list):
            for v in value:
                try:
                    arr.append(self.type(v))
                except Exception as ex:
                    raise ValidationError("Could not cast {} to object of type {}; {}".format(
                        str(v), self.type.__name__, str(ex)))
        # If we got a regular string
        elif isinstance(value, str):
            # If we are breaking up the string based on a delimiter
            if self.delimited:
                for v in value.split(self.delimiter):
                    try:
                        arr.append(self.type(v))
                    except Exception as ex:
                        raise ValidationError("Could not cast {} to object of type {}; {}".format(
                            str(v), self.type.__name__, str(ex)))
            # Else just to to cast the single object into an array
            else:
                try:
                    arr.append(self.type(value))
                except Exception as ex:
                    raise ValidationError("Could not cast {} to object of type {}; {}".format(
                        str(value), self.type.__name__, str(ex)))
        # Otherwise we got an unrecognized object
        else:
            raise ValidationError("Invalid string or string array: {}".format(str(value)))
        return arr


class MoleculeDepctionRequest(BaseDepictorRequest):
    """
    Depiction Request Parser for API v1
    """
    # 'molecule' is V2 compatible and 'val' is V1 compatible
    molecule = fields.String(required=True, allow_none=False)
    width = fields.Integer(required=True, default=400, missing=400)
    height = fields.Integer(required=True, default=400, missing=400)
    # Custom field types
    # Highlight substructure: highlight is API v1 and highlight-ss is API v2 (multiple values allowed)
    highlight_ss = TypedArray(required=False, attribute='highlight-ss', delimited=False, type=str)
    # Hex code or string for coloring the substructure
    highlight_color = Color(required=False, attribute='highlight-color', missing='7070FF')
    # Style in which to render the highlighted substructure
    highlight_style = HighlightStyle(required=False, attribute='highlight-style', missing='default')
    # The input molecule format
    molfmt = fields.String(required=True, missing='smi', validate=lambda f: OEIsReadable(f),
                           error_messages={u'validator_failed': 'Unreadable input molecule format'})
    # For stick, ballandstick, and cogwheel styles, should we "nest" highlighting or keep all the same width
    highlight_nest = fields.Integer(required=False, attribute='highlight-nest', missing=0)
    # Scale by which highlighting can be modified.  0 is default, count up with integers
    highlight_scale = fields.Integer(required=False, attribute='highlight-scale', missing=0)
    # For highlighting atoms by number: whether atoms indices count up by 1 or 0.  Atom numbers start at 0 using OEMol
    # numbering, set to 1 if calling from Pipeline Pilot
    index_start = fields.Integer(required=False, attribute='index-start', missing=0)
    # Comma separated list of atom numbers - we'll convert to int array inside the get method
    # These arrays should be of matched length, each atom set will correspond to the color of the matching index.
    # If the matching index in highlightatomscolor isn't there, the color defaults to the highlight color argument.
    highlight_atoms = TypedArray(required=False, attribute='highlight-atoms', delimited=True, delimiter=',', type=int)
    # Optional arguments for doing atom highlighting by color and atom number
    highlight_atoms_colors = TypedArray(required=False, attribute='highlight-atoms-colors', delimited=True,
                                        delimiter=',', type=str)
    # TODO: Type to parse JSON into array of arrays for highlight-atoms and highlight-atoms-colors
    highlight_atoms_json = TypedArray(required=False, attribute='highlight-atoms-json', delimited=False,
                                      type=lambda n: [])
    # Atom labels are specified as a lists of [atom index, label] tuples e.g. (1, "label 1"), (14, "label 2")
    # TODO: Gotta do this too
    atom_labels = TypedArray(required=False, attribute='atom-labels', delimited=False,
                             type=lambda n: [])
    # Bond labels are specified as a lists of [bond index, label] tuples
    # TODO: Gotta do this too (too)
    bond_labels = TypedArray(required=False, attribute='bond-labels', delimited=False,
                             type=lambda n: [])
    # Color of atom/bond labels
    label_color = Color(required=False, missing='404040')
    # Style of atom/bond labels
    label_style = FontStyle(required=False, missing='default')

    @pre_load(pass_many=False)
    def preprocess_values(self, data):
        # Let size set both width and height
        if 'size' in data:
            data['height'] = data['size']
            data['width'] = data['size']
        # +----------------------------------------------------------------------------------------------------------+
        # | API v1 and v2 PARAMETER COMPATIBILITY                                                                    |
        # |                                                                                                          |
        # | This section make the molecule depiction API v1 and v2 compatible with the same exact Marshmallow Schema |
        # | Need to take the values at index 0 because ImmutableMultiDict always returns an array for each key       |
        # +----------------------------------------------------------------------------------------------------------#
        # API v1 used val instead of molecule
        if 'val' in data:
            data['molecule'] = data.pop('val')
        # API v1 used format instead of imgfmt
        if 'format' in data:
            data['imgfmt'] = data.pop('format')
        # API v1 used highlight instead of highlight-ss
        if 'highlight' in data:
            data['highlight-ss'] = data.pop('highlight')

    # Static block
    # depictor_arg_parser = depictor_base_arg_parser.copy()
    # Only for POST: the molecule string
    # depictor_arg_parser.add_argument('molecule', type=str, default='')
    # The format of the molecule string
    # depictor_arg_parser.add_argument('molfmt', type=str, default='smiles')

    # depictor_arg_parser.add_argument('imgfmt', type=str, default='png', location='args')
    # The image size (assuming a square image)
    # depictor_arg_parser.add_argument('size', type=int, default=400)
    # # The image width - uses size by default in parsing logic below.  If defined, overrides size.
    # depictor_arg_parser.add_argument('width', type=int)
    # # The image height - uses size by default in parsing logic below.  If defined, overrides size.
    # depictor_arg_parser.add_argument('height', type=int)

    # depictor_arg_parser.add_argument('highlight-ss', type=str, action='append')

    # depictor_arg_parser.add_argument('highlight-color',  type=str, default='default')
    # (color, stick, ballandstick, cogwheel)
    # depictor_arg_parser.add_argument('highlight-style',  type=str, default='default')

    # depictor_arg_parser.add_argument('highlight-nest',  type=bool, default=True)

    # depictor_arg_parser.add_argument('highlight-scale', type=int, default=0)

    # depictor_arg_parser.add_argument('index-start', type=int, default=0)

    # depictor_arg_parser.add_argument('highlight-atoms', type=str, action='append', default=[])
    # Atom coloring, index in this array should match index in highlight-atoms
    # depictor_arg_parser.add_argument('highlight-atoms-colors', type=str, action='append', default=[])

    # Optional POST arguments for doing atom highlighting by color and atom number
    # JSON should be a list of dicts (or array of objects) in the following format
    # [{ "atom-indices": [1,2,3], "color": "#0123FF" }, ...]
    # Color is optional, but atom-indices is required
    # depictor_arg_parser.add_argument('highlight-atoms-JSON', type=list, location='json', default=[])

    # POST-Only argument for adding atom labels.
    # depictor_arg_parser.add_argument('atom-labels', type=list, location='json', default=[])
    # POST-Only
    # depictor_arg_parser.add_argument('bond-labels', type=list, location='json', default=[])
    # Color of atom/bondlabels
    # depictor_arg_parser.add_argument('label-color', type=str, default='#404040')
    # Style of atom/bond labels
    # depictor_arg_parser.add_argument('label-style', type=str, default='default')
