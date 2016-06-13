"""Utilites for merging tables prior to import

Contains module functions::
    main(infile_list, outfile)
    main_parse_args()

Examples:

"""

import subprocess
from argparse import ArgumentParser

def main(infile_list, outfile):
    """Uses sort to merge and unique the already sorted file in infile_list
    and stores the results into outfile.

    This takes a ",,"-separated list of sorted files and merges them using the
    unix sort command while removing any duplicate elements.

    Args:
        infile_list (str): ",,"-separated list of the file to merge
        outfile (str): the file to save the result into
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    with open(outfile, 'w') as out:
        cmd1 = ['echo'] + infile_list.split(',,')
        cmd2 = ['xargs', 'sort', '-mu']
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()

def main_parse_args():
    """Processes command line arguments.

    Expects two positional arguments (chunkfile, metadata_json) and number of
    optional arguments. If arguments are missing, supplies default values.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('infile_list', help='",,"-separated list of paths to \
                        sorted files which should be merged')
    parser.add_argument('outfile', help='path to file where the merged results \
                        should be stored')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    main(args.infile_list, args.outfile)
