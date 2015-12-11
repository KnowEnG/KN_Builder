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

def csu(infile, outfile, columns=list()):
    """Performs a cut | sort | uniq on infile using the provided columns and
    stores it into outfile.

    Takes a file in tsv format and sorts by the provided columns using the
    unix sort command and then removes duplicate elements.

    Args:
        infile (str): the file to sort
        outfile (str): the file to save the result into
        columns (list): the columns to use in cut or an empty list if all
                        columns should be used
    Returns:
    """
    with open(outfile, 'w') as out:
        cmd2 = ['sort', '-u']
        if len(columns):
            cmd1 = ['cut', '-f', ','.join(map(str, columns)), infile]
        else:
            cmd1 = ['cat', infile]
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()

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
    src_code_dir = os.path.join(args.local_dir, args.code_path, args.src_path)
    sys.path.append(src_code_dir)
    src_module = __import__(version_dict['source'])
    SrcClass = src_module.get_SrcClass(args)
    if not version_dict['is_map']:
        SrcClass.table(chunkfile, version_dict)
        #csu(chunkfile.replace('rawline', 'edge'))

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
