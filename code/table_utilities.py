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
import subprocess
import os
import config_utilities as cf
from argparse import ArgumentParser

def sort(tablefile, c1='5', c2='9'):
    """Takes a tabled file and sorts it by the defined two columns.
    
    Takes a file in table format and sorts by the provided columns using the
    unix sort command. By detault, this sorts by the two columns which contain
    the species for node1 and the species for node2.
    
    Args:
        tablefile (str): the file to sort
        c1 (str): primary column to sort by
        c2 (str): secondary column to sort by
    Returns:
    """
    cmd = 'sort -k ' + c1 + ',' + c1 + ' -k ' + c2 + ',' + c2 + ' ' + tablefile
    outfile = os.path.dirname(tablefile) + os.sep + 'sorted_' + \
        os.path.basename(tablefile)
    subprocess.call(cmd + ' > ' + outfile, shell=True)

def main(chunkfile, version_json, args=cf.config_args()):
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
    src_code_dir = os.path.join(args.local_dir, args.code_path, 'srcClass')
    sys.path.append(src_code_dir)        
    src_module = __import__(version_dict['source'])
    SrcClass = src_module.get_SrcClass(args)
    if not version_dict['is_map']:
        SrcClass.table(chunkfile, version_dict)
        sort(chunkfile.replace('rawline', 'edge'))

def main_parse_args():
    """Processes command line arguments.

    If argument is missing, supplies default     value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('chunkfile', help='path to a single chunk file produced \
                        in fetch, e.g. biogrid.PPI.rawline.1.txt')
    parser.add_argument('metadata_json', help='json file produced from check, \
                        e.g. file_metadata.json')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    main(args.chunkfile, args.metadata_json, args)
