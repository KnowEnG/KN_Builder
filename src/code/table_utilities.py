"""Utiliites for fetching and chunking a source for the Knowledge Network (KN)
that has been updated.

Contains module functions::

    csu(infile, outfile, columns=list())
    main_parse_args()
    main(chunkfile, version_json, args=None)

Examples:
    To run table on a single source (e.g. dip) after fetch complete::

        $ cd data/dip/PPI
        $ python3 ../../../code/table_utilities.py chunks/dip.PPI.raw_line.1.txt \
            file_metadata.json

    To view all optional arguments that can be specified::

        $ python3 code/table_utilities.py -h
"""

import json
import sys
import subprocess
import os
from argparse import ArgumentParser
import config_utilities as cf

def csu(infile, outfile, columns=None):
    """Performs a cut | sort | uniq on infile using the provided columns and
    stores it into outfile.

    Takes a file in tsv format and sorts by the provided columns using the
    unix sort command and then removes duplicate elements.

    Args:
        infile (str): the file to sort
        outfile (str): the file to save the result into
        columns (list): the columns to use in cut or an empty list if all
                        columns should be used
    """
    if columns is None:
        columns = []
    with open(outfile, 'w') as out:
        cmd2 = ['sort', '-u']
        if columns:
            cmd1 = ['cut', '-f', ','.join(map(str, columns)), infile]
        else:
            cmd1 = ['cat', infile]
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()

def main(chunkfile, version_json, args=None):
    """Tables the source:alias described by version_json.

    This takes the path to a chunked (see fetch_utilities.chunk)  raw_line file
    and it's correpsonding version_json (source.alias.json) and runs the
    source specific table command (see SrcClass.table) if the alias is a data
    file. If it is a mapping file, it does nothing:

        raw_line (line_hash, line_num, file_id, raw_line)
        table_file (line_hash, n1name, n1hint, n1type, n1spec,\
                    n2name, n2hint, n2type, n2spec, et_hint, score,\
                    table_hash)
        edge_meta (line_hash, info_type, info_desc)
        node_meta (node_id, \
                   info_type (evidence, relationship, experiment, or link), \
                   info_desc (text))
        node (node_id, n_alias, n_type)

    Args:
        version_json (str): path to a chunk file in raw_line format
        version_json (str): path to a json file describing the source:alias
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    src_code_dir = os.path.join(args.code_path, args.src_path)
    sys.path.append(src_code_dir)
    src_module = __import__(version_dict['source'])
    SrcClass = src_module.get_SrcClass(args)
    if not version_dict['is_map']:
        SrcClass.table(chunkfile, version_dict)
        #csu(chunkfile.replace('raw_line', 'edge'))

def main_parse_args():
    """Processes command line arguments.

    Expects two positional arguments (chunkfile, metadata_json) and number of
    optional arguments. If arguments are missing, supplies default values.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('chunkfile', help='path to a single chunk file produced \
                        in fetch, e.g. dip.PPI.raw_line.1.txt')
    parser.add_argument('metadata_json', help='json file produced from check, \
                        e.g. file_metadata.json')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    main(args.chunkfile, args.metadata_json, args)
