"""Utiliites for mapping the gene identifiers in an edge file.

Contains module functions::

    map_list(namefile, args=None)
    main_parse_args()
    main(edgefile, args=None)

Attributes:
    DEFAULT_HINT (str): the default mapping hint for converting identifiers
    DEFAULT_TAXON (int): the default taxon id to use for converting identfiers

Examples:
    To run conv on a single source (e.g. dip) after table complete::

        $ python3 code/conv_utilities.py data/dip/PPI/chunks/dip.PPI.edge.1.txt

    To run conv on a file of gene names::

        $ python3 code/conv_utilities.py -m LIST list_of_gene_names.txt

    To view all optional arguments that can be specified::

        $ python3 code/conv_utilities.py -h
"""

import config_utilities as cf
import redis_utilities as ru
import table_utilities as tu
import import_utilities as iu
from argparse import ArgumentParser
import csv
import sys
import hashlib
import os

csv.field_size_limit(sys.maxsize)

DEFAULT_HINT = ''
DEFAULT_TAXON = 9606

def main(edgefile, args=None):
    """Maps the nodes for the source:alias edgefile.

    This takes the path to an edgefile (see table_utilities.main) and maps
    the nodes in it using the Redis DB. It then outputs an edge_mapped file in
    the format (n1, n2, line_checksum, edge_type, weight, status, status_desc),
    where status is production if both nodes mapped and unmapped otherwise.

    Args:
        edgefile (str): path to an edgefile to be mapped
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    if 'lincs.level4' in edgefile or 'lincs.exp_meta' in edgefile:
        if os.path.isfile(edgefile.replace('conv', 'node')):
            iu.import_pnode(edgefile.replace('conv', 'node'), args)
        iu.import_edge(edgefile, args)
        return
    rdb = ru.get_database(args)
    conv_file = edgefile.replace('edge', 'conv')
    status_file = edgefile.replace('edge', 'status')
    uc_file = edgefile.replace('edge', 'unique_conv')
    ue2l_file = edgefile.replace('edge', 'unique_edge2line')
    us_file = edgefile.replace('edge', 'unique_status')
    with open(edgefile, 'r') as infile, \
        open(conv_file, 'w') as e_map, \
        open(status_file, 'w') as e_stat:
        reader = csv.reader(infile, delimiter = '\t')
        writer = csv.writer(e_map, delimiter = '\t', lineterminator='\n')
        s_writer = csv.writer(e_stat, delimiter = '\t', lineterminator='\n')
        for line in reader:
            (n1, hint, ntype, taxid) = line[1:5]
            if ntype == 'gene':
                n1_map = ru.conv_gene(rdb, n1, hint, taxid)
            else:
                n1_map = n1
            (n2, hint, ntype, taxid) = line[5:9]
            if ntype == 'gene':
                n2_map = ru.conv_gene(rdb, n2, hint, taxid)
            else:
                n2_map = n2
 #           print("\t".join([taxid, hint, n1, n1_map, n2, n2_map]))
            chksum = line[0] #line chksum
            et_map = line[9]
            weight = line[10]
            t_chksum = line[11] #raw edge chksum
            hasher = hashlib.md5()
            hasher.update('\t'.join([n1_map, n2_map, et_map]).encode())
            e_chksum = hasher.hexdigest()
            if 'unmapped' in n1_map:
                status = 'unmapped'
                status_desc = n1_map
            elif 'unmapped' in n2_map:
                status = 'unmapped'
                status_desc = n2_map
            else:
                status = 'production'
                status_desc = 'mapped'
                writer.writerow([n1_map, n2_map, et_map, weight, e_chksum, \
                    chksum])
            s_writer.writerow([n1_map, n2_map, et_map, weight, e_chksum, \
                chksum, t_chksum, status, status_desc])
    tu.csu(conv_file, uc_file, [1, 2, 3, 4, 5])
    tu.csu(conv_file, ue2l_file, [5, 6])
    tu.csu(status_file, us_file)
    #iu.import_edge(uc_file, args)
    iu.import_status(status_file, args)

def map_list(namefile, args=None):
    """Maps the nodes for the provided namefile.

    This takes the path to an namefile and maps the nodes in it using the Redis
    DB. It then outputs an mapped file in the format (mapped, original).

    Args:
        namefile (str): path to an namefile to be mapped
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    rdb = ru.get_database(args)
    with open(namefile, 'r') as infile, \
        open(os.path.splitext(namefile)[0] + '.mapped.txt', 'w') as n_map:
        reader = csv.reader(infile, delimiter = '\t')
        writer = csv.writer(n_map, delimiter = '\t', lineterminator='\n')
        for line in reader:
            orig = line[0]
            mapped = ru.conv_gene(rdb, orig, args.source_hint, args.taxon)
            writer.writerow([mapped, orig])

def main_parse_args():
    """Processes command line arguments.

    Expects one positional argument (infile) and number of optional
    arguments. If arguments are missing, supplies default values.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('infile', help='path to the file to be mapped. If mode \
                        is LIST, it should contain one identifer on each line. \
                        If mode is EDGE, it should be a single edge file \
                        produced in table, e.g. biogrid.PPI.edge.1.txt')
    parser.add_argument('-m', '--mode', help='mode for running convert. "EDGE" \
                        if mapping and edge file, or "LIST" to map a list of \
                        names to the stable ids used in the Knowledge Network',
                        default='EDGE')
    parser.add_argument('-sh', '--source_hint', help='suggestion for ID source \
                        database used to resolve ambiguities in mapping',
                        default=DEFAULT_HINT)
    parser.add_argument('-t', '--taxon', help='taxon id of species of all gene \
                        names', default=DEFAULT_TAXON)
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    if args.mode == 'EDGE':
        main(args.infile, args)
    elif args.mode == 'LIST':
        map_list(args.infile, args)
    else:
        print(args.mode + ' is not a valid mode. Must be EDGE or LIST.')
