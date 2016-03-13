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

from flask.ext.restful import reqparse

########################################################################################################################
#                                                                                                                      #
#                                       Common parser for images in v1 APIs                                            #
#                                                                                                                      #
########################################################################################################################

depictor_base_arg_parser_v1 = reqparse.RequestParser()
# If we should reparse connectivity, aromaticity, stereochemistry, hydrogens and formal charges
depictor_base_arg_parser_v1.add_argument('reparse', type=bool, default=False, location='args')
# If we should keep the molecule title (if using an SDF or other file format with titles)
depictor_base_arg_parser_v1.add_argument('keeptitle', type=bool, default=False, location='args')
# The title location (top or bottom), if we have a title
depictor_base_arg_parser_v1.add_argument('titleloc', type=str, default='top', location='args')
# The image format (png, svg, pdf, etc.)
depictor_base_arg_parser_v1.add_argument('format', type=str, default='png', location='args')
# The molecule title
depictor_base_arg_parser_v1.add_argument('title', type=str, default='', location='args')
# If the molecule is gzipped then base64 encoded
depictor_base_arg_parser_v1.add_argument('gz', type=bool, default=False, location='args')
# Bond scales with the size of the image
depictor_base_arg_parser_v1.add_argument('scalebonds', type=bool, default=False, location='args')
# Background color of image
depictor_base_arg_parser_v1.add_argument('background', type=str, default="#ffffff00", location='args')
# Debug mode
depictor_base_arg_parser_v1.add_argument('debug', type=bool, default=False, location='args')

########################################################################################################################
#                                                                                                                      #
#                                       Common parser for images in v2 APIs                                            #
#                                                                                                                      #
########################################################################################################################

depictor_base_arg_parser_v2 = reqparse.RequestParser()
# If we should reparse connectivity, aromaticity, stereochemistry, hydrogens and formal charges
depictor_base_arg_parser_v2.add_argument('reparse', type=bool, default=False)
# If we should keep the molecule title (if using an SDF or other file format with titles)
depictor_base_arg_parser_v2.add_argument('keep-title', type=bool, default=False)
# The title location (top or bottom), if we have a title
depictor_base_arg_parser_v2.add_argument('titleloc', type=str, default='top')
# The image format (png, svg, pdf, etc.)
depictor_base_arg_parser_v2.add_argument('image-format', type=str, default='png')
# The molecule title
depictor_base_arg_parser_v2.add_argument('title', type=str, default='')
# If the molecule is gzipped then base64 encoded
depictor_base_arg_parser_v2.add_argument('gz', type=bool, default=False)
# Bond scales with the size of the image
depictor_base_arg_parser_v2.add_argument('scale-bonds', type=bool, default=False)
# Background color of image
depictor_base_arg_parser_v2.add_argument('background', type=str, default="#ffffff00")
# Debug mode
depictor_base_arg_parser_v2.add_argument('debug', type=bool, default=False)