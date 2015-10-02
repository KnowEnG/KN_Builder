"""Utiliites for mapping the gene identifiers in an edge file.

Classes:

Functions:
    main(edgefile, args) -> : takes the path to an edge file in the table
        format (see table_utilities) and maps the nodes in each line. It also
        formats the line in a similar manner to the edge table in MySQL and
        determines if the status of the line. It returns nothing.

Variables:
"""

import config_utilities as cf
import redis_utilities as ru
from argparse import ArgumentParser
import csv
import hashlib

def main(edgefile, args=cf.config_args()):
    """Maps the nodes for the source:alias edgefile.

    This takes the path to an edgefile (see table_utilities.main) and maps
    the nodes in it using the Redis DB. It then outputs an edge_mapped file in
    the format (n1, n2, line_checksum, edge_type, weight, status, status_desc),
    where status is production if both nodes mapped and unmapped otherwise.

    Args:
        edgefile (str): path to an edgefile to be mapped
        args (argparse object): arguments as populated namespace

    Returns:
    """
    rdb = ru.get_database(args)
    with open(edgefile, 'r') as infile:
        reader = csv.reader(infile, delimiter = '\t')
        e_map = open(edgefile.replace('edge', 'conv'), 'w')
        e_stat = open(edgefile.replace('edge', 'status'), 'w')
        writer = csv.writer(e_map, delimiter = '\t')
        s_writer = csv.writer(e_stat, delimiter = '\t')
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
            chksum = line[0]
            et_map = line[9]
            weight = line[10]
            t_chksum = line[11]
            if 'unmapped' in n1_map:
                status = 'unmapped'
                status_desc = n1_map
            elif 'unmapped' in n2_map:
                status = 'unmapped'
                status_desc = n2_map
            else:
                status = 'production'
                status_desc = ''
                hasher = hashlib.md5()
                hasher.update('\t'.join([n1_map, n2_map, et]))
                e_chksum = hasher.hexdigest()
                writer.writerow([n1_map, n2_map, chksum, et_map, weight,
                                e_chksum])
            s_writer.writerow([t_chksum, n1_map, n2_map, et_map, status,
                            status_desc])
        e_stat.close()
        e_map.close()

def main_parse_args():
    """Processes command line arguments.

    If argument is missing, supplies default     value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('edgefile', help='path to a single edge file produced \
                        in table, e.g. biogrid.PPI.edge.1.txt')
    parser.add_argument('-rh', '--redis_host', help='url of Redis db',
                        default=cf.DEFAULT_REDIS_URL)
    parser.add_argument('-rp', '--redis_port', help='port for Redis db',
                        default=cf.DEFAULT_REDIS_PORT)
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    main(args.edgefile, args)
