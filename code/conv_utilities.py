"""Utiliites for mapping the gene identifiers in an edge file.

Contains module functions::

    map_list(namefile, args=None)
    main_parse_args()
    main(tablefile, args=None)

Attributes:
    DEFAULT_HINT (str): the default mapping hint for converting identifiers
    DEFAULT_TAXON (int): the default taxon id to use for converting identfiers

Examples:
    To run conv on a single source (e.g. dip) after table complete::

        $ python3 code/conv_utilities.py data/dip/PPI/chunks/dip.PPI.edge.1.txt

    To run conv on a file of gene names::

        $ python3 code/conv_utilities.py -mo LIST list_of_gene_names.txt

    To view all optional arguments that can be specified::

        $ python3 code/conv_utilities.py -h
"""

import csv
import sys
import hashlib
import os
import json
from argparse import ArgumentParser
from collections import defaultdict
import config_utilities as cf
import redis_utilities as ru
import table_utilities as tu
import import_utilities as iu

csv.field_size_limit(sys.maxsize)

DEFAULT_HINT = ''
DEFAULT_TAXON = 9606

def main(tablefile, args=None):
    """Maps the nodes for the source:alias tablefile.

    This takes the path to an tablefile (see table_utilities.main) and maps
    the nodes in it using the Redis DB. It then outputs a status files in
    the format (table_hash, n1, n2, edge_type, weight, edge_hash, line_hash,
    status, status_desc), where status is production if both nodes mapped and
    unmapped otherwise. It also outpus an edge file which all rows where status
    is production, in the format (edge_hash, n1, n2, edge_type, weight), and
    and edge2line file in the formate (edge_hash, line_hash).

    Args:
        tablefile (str): path to an tablefile to be mapped
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    if 'lincs.level4' in tablefile or 'lincs.exp_meta' in tablefile:
        if os.path.isfile(tablefile.replace('conv', 'node')):
            iu.import_pnode(tablefile.replace('conv', 'node'), args)
        iu.import_edge(tablefile, args)
        return
    rdb = ru.get_database(args)
    edge_file = tablefile.replace('table', 'edge')
    status_file = tablefile.replace('table', 'status')
    ue_file = tablefile.replace('table', 'unique.edge')
    ue2l_file = tablefile.replace('table', 'unique.edge2line')
    us_file = tablefile.replace('table', 'unique.status')
    src_data_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
    species_file = os.path.join(src_data_dir, 'species', 'species.json')
    with open(species_file, 'r') as infile:
        species_dict = json.load(infile)
    supported_taxids = ['unknown'] + list(species_dict.values())
    with open(tablefile, 'r') as infile, \
        open(edge_file, 'w') as edge, \
        open(status_file, 'w') as e_stat:
        reader = csv.reader(infile, delimiter='\t')
        s_writer = csv.writer(e_stat, delimiter='\t', lineterminator='\n')
        e_writer = csv.writer(edge, delimiter='\t', lineterminator='\n')
        to_map = defaultdict(list)
        for line in reader:
            (n1, hint, ntype, taxid) = line[1:5]
            if ntype == 'gene' and taxid in supported_taxids:
                to_map[hint, taxid].append(n1)
            (n2, hint, ntype, taxid) = line[5:9]
            if ntype == 'gene' and taxid in supported_taxids:
                to_map[hint, taxid].append(n2)
        infile.seek(0)
        mapped = {k: {n: m for m, n in zip(ru.conv_gene(rdb, v, k[0], k[1]), v)} for k, v in
                  to_map.items()}
        for line in reader:
            (n1, hint, ntype, taxid) = line[1:5]
            if ntype == 'gene':
                if taxid not in supported_taxids:
                    n1_map = 'unmapped-unsupported-species'
                else:
                    n1_map = mapped[hint, taxid][n1]
            else:
                n1_map = n1
            (n2, hint, ntype, taxid) = line[5:9]
            if ntype == 'gene':
                if taxid not in supported_taxids:
                    n2_map = 'unmapped-unsupported-species'
                else:
                    n2_map = mapped[hint, taxid][n2]
            else:
                n2_map = n2
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
                e_writer.writerow([e_chksum, n1_map, n2_map, et_map, weight])
            s_writer.writerow([t_chksum, n1_map, n2_map, et_map, weight, e_chksum, \
                chksum, status, status_desc])
    tu.csu(edge_file, ue_file)
    tu.csu(status_file, us_file)
    tu.csu(us_file, ue2l_file, [6, 7])

def map_list(namefile, args=None):
    """Maps the nodes for the provided namefile.

    This takes the path to an namefile and maps the nodes in it using the Redis
    DB. It then outputs an mapped file in the format (mapped, original).

    Args:
        namefile (str): path to an namefile to be mapped
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = main_parse_args()
    rdb = ru.get_database(args)
    with open(namefile, 'r') as infile, \
        open(os.path.splitext(namefile)[0] + '.node_map.txt', 'w') as n_map:
        reader = csv.reader(infile, delimiter='\t')
        writer = csv.writer(n_map, delimiter='\t', lineterminator='\n')
        mapped = ru.get_node_info(rdb, [line[0] if line else '' for line in reader], None,
                                  args.source_hint, args.taxon)
        writer.writerows(mapped)


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
    parser.add_argument('-mo', '--mode', help='mode for running convert. "EDGE" \
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
