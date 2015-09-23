"""Utiliites for importing data into the Knowledge Network.

Classes:

Functions:
    import(module) ->: takes a SrcClass object and imports it into the
    Knowledge Network.

Variables:
"""

import json
import sys
import config_utilities as cf
from argparse import ArgumentParser

def db_import(version_json, args=cf.config_args()):
    """Runs the import function on the alias described by version_json.

    This runs the import function on the file described by version_json. The
    end result is that the processed data is added to the Knowledge Network.

    Returns:
    """
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    if version_dict['source'] == 'ensembl':
        src_module = __import__('ensembl')
        src_module.db_import(version_json, args)

def main_parse_args():
    """Processes command line arguments.

    If argument is missing, supplies default value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('metadata_json', help='json file produced from check, \
                        e.g. file_metadata.json')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    db_import(args.metadata_json, args)



