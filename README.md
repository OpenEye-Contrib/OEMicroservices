# OEMicroservices

A collection of useful microservices developed using the OpenEye toolkits and deployed with Flask and Flask-RESTful.

## Installation

**Prerequisites:** Flask, Flask-RESTful, and the OpenEye Toolkits version 2015.Feb or newer (http://www.eyesopen.com) 
with a valid license. If you see an error saying that a module could not be imported or does not exist, it is likely
that you are missing at least one prerequisite.

Usable as a standalone application or can be installed as a Python package.

To install into Python as a package:

    python setup.py install
   
To uninstall

    pip uninstall OEMicroservices

Tested in Anaconda Python 2.7.9 and 3.4.3.

## Running in Docker

It's not on Dockerhub yet, so you need to build the image first:
`docker build -t oe-microservices .`
And then run: `docker run -p 5000:5000 -v /path/to/oe_license.txt_:/tmp/oe_license.txt:ro oe-microservices`

## Usage

### Standalone Application

From the OEMicroservices root folder, simply run `python server.py`. This file may be modified and `app.run(...)` 
changed with your Flask server preferences. Note that Flask recommends not using its server in production. See the
"Python Package" section for an example of installing OEMicroservices and using it with the Gunicorn web server.

### Python Package

The *server.py* script can be used from any directory when the OEMicroservices package is installed. Alternatively
the underlying services can be used directly from another Pythong WSGI web server like Gunicorn.

Example running with Gunicorn in threaded mode when the OEMicroservices package is installed, which may be executed in 
any directory:
    
    gunicorn oemicroservices.api:app --bind 0.0.0.0:5000 --threads 5

Note that in Python 2.x you might need the "trollius" package to use multiple Gunicorn threads.

### API

**IMPORTANT:** The complete API can be found in the *docs* directory.

Some basic examples are provided here and they all assume that you are running on a local server (127.0.0.1) on port 
5000. If you are running on another server, you'll want to replace the 127.0.0.1:5000 with the correct server/port 
combination. Without further ado, here  are some simple examples:

#### Small Molecule Rendering (GET)
*URL:* http://127.0.0.1:5000/v1/depict/structure/{format}?val={molecule_string}

Where `{format}` is the format of the `{molecule_string}` defined by the *val* query parameter. Both `{format}` and 
`{molecule_string}` are required. The following is a list of possible values for `{format}`:

- cdx : ChemDraw file
- ism : Canonical isomeric SMILES
- mdl : Same as mol
- mmod : MacroModel file
- mol : MDL MOL file (CTAB)
- mol2 : Tripos MOL2 file
- oeb : OpenEye binary file
- pdb : Protein Data Bank file
- sdf : MDL SD file
- skc : Accelrys Draw sketch file
- smi : Same as ism
- smiles : Same as ism
- usm : Arbitrary SMILES
- xyz : XYZ chemical file

The *val* query parameter that defines `{molecule_string}` is the complete URL encoded molecule string. For SMILES, this 
could be as simple as just c1ccccc1; but for PDB, this would be the entire PDB file URL encoded. Be careful of the 2083 
character URL limit. If you think you might exceed this limit, use the POST method for this resource instead of GET.

Render the structure of Januvia (PNG default): 

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F

Render a larger Januvia PNG and scale the bonds with the size of the structure:

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F&height=800&width=800&scalebonds=true

Render the structure of Januvia as an SVG:

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F&format=svg

Render the structure of Januvia as a PDF with a caption under the image:

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F&format=pdf&title=Januvia&titleloc=bottom

Render the structure of Januvia with a substructure highlight in stick mode:

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F&highlight=C1CNCcn1&highlightstyle=stick

Render the structure of Januvia with a partially transparent purple-ish looking background:

    http://127.0.0.1:5000/v1/depict/structure/smiles?val=Fc1cc(c(F)cc1F)C%5BC%40%40H%5D(N)CC(%3DO)N3Cc2nnc(n2CC3)C(F)(F)F&background=3300f520

Render the structure of Januvia using a gzipped and base64 encoded SD file (Note the *gz=true* parameter implies 
gzipping, then base64 encoding, then finally URL encoding):

    http://127.0.0.1:5000/v1/depict/structure/sdf?format=svg&gz=true&val=H4sIAIZng1UC/6VVMW7DMAzc/QoNXSOQlChKc9KiS9OtPyjQpf9fS1m205gCWiuGEQhn8nJ3lOXJudP78/nr8/sECTMyASNdpslRcQGdA1evtrjdpRT3QQAw6cMTegk51brgSwlSV%2BD1KbgXt%2Bvs3jML%2BQRxYYn3LOdjLGkWTQ%2BwqIKkFqtzX3JbHWeJPkSkVUtbHWdhrzOBVYvEsXSrlrylm%2BJwLsJlnTTjOEucFcQ9y8uxGQm03vEZkWeV0HpjoX4u%2BDcLAi0zCnyn5fWIIyizoxP4IAy/WK7/Z6lvIy0sAHcsB3IBn5NsuayrARaB2HLZsbz/m2Xt6K2uR1hyyksvg4ztF1fTTVu6MJaungephNx6A%2BKgo%2BApc25aGEIaY9m06M4JmOOjuaD2Cj44I2VRR2On922XzFo4j7Ho2wiU29tNqfAoS%2BE13ZKAh846nZF%2BlmU5rySPfQNUi%2B41aScN0ZgWHSztDsRphvL8u0eDrVUo2lqF2NYqlLqoWAaZNexrFSoWjQ7BoAohWhQdNse4Q0O3NlpU/816UwiTcVFRsbXiiHsoWscKoXWsEIUuCkaDQmRzUIjI1lKPVyGyOSjUcVEZ7IwVIumiuYsax2/OPV8v05Ne0w9dF3x55QoAAA%3D%3D

#### Small Molecule Rendering (POST)
*URL:* http://127.0.0.1:5000/v1/depict/structure/{format}

A POST to this resource does not require a *val* query parameter, because the raw molecule file is expected in the body 
of the POST. This allows more verbose molecule files to be rendered as it does not suffer from the 2083 character URL 
length limit.

Essentially all of the examples above work here, except that instead of *val*=..., you just shove that string into the
POST body. Here is an example raw HTTP POST request for Januvia in SD format without the gzipping and base64 encoding:

    POST http://127.0.0.1:5000/v1/depict/structure/sdf?format=svg HTTP/1.1
    Content-Type: text/plain
    Host: 127.0.0.1:5000
    Content-Length: 2853
    
    
      -OEChem-06181521172D
    
     29 31  0     1  0  0  0  0  0999 V2000
       -1.7386    3.9937    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
       -2.6046    3.4937    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -2.6060    2.4937    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -3.4699    1.9899    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -4.3412    2.4912    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -5.2050    1.9874    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
       -4.3486    3.4964    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -3.4759    3.9951    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -3.4744    4.9951    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
       -3.4670    0.9899    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -2.5995    0.4924    0.0000 C   0  0  1  0  0  0  0  0  0  0  0  0
       -2.1020    1.3599    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
       -3.0970   -0.3750    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
       -1.7320   -0.0050    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -0.8675    0.4975    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       -0.8704    1.4975    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
        0.0000    0.0000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
        0.8680    0.5079    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        1.7360   -0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        2.6938    0.3110    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
        3.2858   -0.5036    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
        2.6938   -1.3184    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        1.7360   -1.0071    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
        0.8680   -1.5037    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        0.0000   -1.0058    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        3.0028   -2.2695    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
        3.9538   -1.9605    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
        2.0517   -2.5784    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
        3.3117   -3.2205    0.0000 F   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  1  0  0  0  0
      2  8  2  0  0  0  0
      2  3  1  0  0  0  0
      3  4  2  0  0  0  0
      4  5  1  0  0  0  0
      5  6  1  0  0  0  0
      5  7  2  0  0  0  0
      7  8  1  0  0  0  0
      8  9  1  0  0  0  0
      4 10  1  0  0  0  0
     10 11  1  0  0  0  0
     11 12  1  1  0  0  0
     11 13  1  0  0  0  0
     11 14  1  0  0  0  0
     14 15  1  0  0  0  0
     15 16  2  0  0  0  0
     15 17  1  0  0  0  0
     17 25  1  0  0  0  0
     17 18  1  0  0  0  0
     18 19  1  0  0  0  0
     19 23  1  0  0  0  0
     19 20  2  0  0  0  0
     20 21  1  0  0  0  0
     21 22  2  0  0  0  0
     22 23  1  0  0  0  0
     23 24  1  0  0  0  0
     24 25  1  0  0  0  0
     22 26  1  0  0  0  0
     26 27  1  0  0  0  0
     26 28  1  0  0  0  0
     26 29  1  0  0  0  0
    M  END
    $$$$

#### Protein-Ligand Interaction Map (POST)
*URL:* http://127.0.0.1:5000/v1/depict/interaction

A POST to this resource expects a JSON string in the POST body with the following schema:

```json
{
  "ligand": {
    "value": "A string that contains the ligand structure [REQUIRED]",
    "format": "The file format of the ligand string (e.g. sdf, pdb, oeb, etc.) [REQUIRED]",
    "gz": "If the ligand string is gzipped and then b64 encoded"
  },
  "receptor": {
    "value": "A string that contains the receptor structure [REQUIRED]",
    "format": "The file format of the receptor string (e.g. sdf, pdb, oeb, egc.) [REQUIRED]",
    "gz": "If the receptor string is gzipped and then b64 encoded"
  }
}
```

The *value* and *format* variables are necessary for both the ligand and receptor. The *value* variables contain the
raw (JSON encoded) molecule file strings with file format specified by *format*. Many of the same query string
parameters are valid for this resource (e.g. height, width). The legend is shown by default and can be hidden via the 
legend boolean query parameter (e.g. http://...?legend=false). Don't forget to set the Content-Type of the HTTP POST to 
application/json!

#### Protein-Ligand Interaction Map With Ligand Search (POST)
*URL:* http://127.0.0.1:5000/v1/depict/interaction/search/{format}

This resource is different from the one above because the POST expects only the raw molecule file (no special encodings
necessary), and we have our old friend and required parameter `{format}` back in the path, which specifies the molecular
file format of the POST. Any of the molecular file formats listed above in the "Small Molecule Rendering (GET)"
section can be used here as well.

There are three parameters in the query string that can be used in any combination to locate the ligand in the file:

* *resn* - Residue name
* *resi* - Residue number
* *chain* - Chain ID

These are borrowed from the PyMOL selection syntax, so don't be angry with me if you don't like them!

Example locating Suvorexant in 4S0V (any of these will work providing the raw PDB in the POST):
    http://127.0.0.1:5000/v1/depict/interaction/search/pdb?resn=SUV
    http://127.0.0.1:5000/v1/depict/interaction/search/pdb?resi=2001
    http://127.0.0.1:5000/v1/depict/interaction/search/pdb?resi=2001&chain=A
    http://127.0.0.1:5000/v1/depict/interaction/search/pdb?resn=SUV&resi=2001&chain=A

Lots of familiar query string parameters are valid here (e.g. height, width), the legend query parameter described
above, and the similarly familiar gz (e.g. gz=true) parameter to indicate if the POST body has been gzipped and 
base64 encoded.

#### Molecular File Format Conversion (POST)

A POST to this resource expects a JSON string in the POST body with the following schema:

```json
{
  "molecule": {
    "value": "A string that contains the input molecule file string [REQUIRED]",
    "input": {
      "format": "The file format of the input molecule string (e.g. sdf, pdb, oeb, etc.) [REQUIRED]",
      "gz": "If the input molecule string is gzip + b64 encoded"
    },
    "output": {
      "format": "The file format of the output molecule string (e.g. sdf, pdb, oeb, etc.) [REQUIRED]",
      "gz": "If the output molecule string should be gzip + b64 encoded"
    }
  }
}
```

And returns a JSON response with the following schema:

```json
{
  "molecule": {
      "value": "A string containing the output molecule file string",
      "format": "The output file format",
      "gz": "If the output molecule string is gzip + b64 encoded"
  }
}
```

There are no query string parameters available for this resource.

## Contributing

Fork it and submit a pull request!

## History

**2015-07-09 - Version 1.2**

- Replaced file type dictionary with OEGetFileType
- Updated tests to reflect changes in file type handling
- Fixed issue around OEGetFileType and Python 2/3 unicode vs UTF-8 strings

**2015-06-20 - Version 1.1**

Added documentation:

- Swagger.io API description in YAML and auto-generated JSON

Minor API tweaks to molecule and interaction depictors for consistency:

- keepTitle query parameter changed to keeptitle
- titleLoc query parameter changed to titleloc
- scaleBonds query parameter changed to scalebonds

Minor API tweaks to MoleculeDepictor for consistency:

- color query parameter changed to highlightcolor
- style query parameter changed to highlightstyle

**2015-06-18 - Version 1.0**

The initial release provides the following capabilities:

- Small molecule rendering
- Protein-ligand interaction map rendering
- Protein-ligand interaction map rendering with ligand search
- Molecule file format conversion

## Credits

Created by Scott Arne Johnson <scott.johnson6@merck.com>.

## License

Distributed under the Apache License 2.0. See the LICENSE file for details.