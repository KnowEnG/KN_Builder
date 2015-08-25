"""Utiliites for fetching and chunking a source for the Knowledge Network (KN)
that has been updated.

Classes:

Functions:
    table(version_dict, chunkfile) -> : takes a dictionary object version_dict
        and the path to a file. Determines if the described alias is a data
        file. If so it runs the source specific table function on it. In either
        case it returns nothing.

Variables:
"""

import json
import sys

def main(chunkfile, version_json):
    """Tables the source:alias described by version_json.

    This takes the path to a chunked (see fetch_utilities.chunk)  rawline file
    and it's correpsonding version_json (source.alias.json) and runs the
    source specific table command (see SrcClass.table) if the alias is a data
    file. If it is a mapping file, it does nothing.

    Args:
        version_json (str): path to a json file describing the source:alias

    Returns:
    """
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    src_module = __import__(version_dict['source'])
    SrcClass = src_module.get_SrcClass()
    if not version_dict['is_map']:
        SrcClass.table(chunkfile, version_dict)
    return

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
