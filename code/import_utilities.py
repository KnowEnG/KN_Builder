"""Utiliites for importing data into the Knowledge Network.

Classes:

Functions:
    import(module) ->: takes a SrcClass object and imports it into the
    Knowledge Network.

Variables:
"""

import json
import sys

def db_import(version_json):
    """Runs the import function on the alias described by version_json.

    This runs the import function on the file described by version_json. The
    end result is that the processed data is added to the Knowledge Network.

    Returns:
    """
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    if version_dict['source'] == 'ensembl':
        src_module = __import__('ensembl')
        src_module.db_import(version_json)

if __name__ == "__main__":
    db_import(sys.argv[1])


