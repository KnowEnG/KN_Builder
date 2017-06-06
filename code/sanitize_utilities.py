#!/usr/bin/env python3

import collections

VALID_NORMALIZE_METHODS = [None, 'type']
DEFAULT_NORMALIZE_METHOD = VALID_NORMALIZE_METHODS[1]

# These mean, as indicated by the required uniqueness condition on edges:
# 'type': unique based on {node1, node2, type}
# 'node': unique based on {node1, node2}
# 'exact': unique based on {node1, node2, weight, type}
# They are listed in order of preference/likelihood.
VALID_DROP_DUPLICATES_METHOD = [None, 'type', 'node', 'exact']
DROP_DUPLICATES_METHOD = VALID_DROP_DUPLICATES_METHOD[1]


def add_config_args(parser): #NEW, UNDOC
    """
    Add arguments specific to this module.

    Parameters:
        parser (argparse.parser): the parser to add arguments to

    Returns:
        argparse.parser: the parser with the arguments added
    """
    parser.add_argument('-und', '--make_undirected', action='store_true')
    parser.add_argument('-unw', '--make_unweighted', action='store_true')
    parser.add_argument('-norm', '--normalize', action='store_true')
    parser.add_argument('-normm', '--normalize_method', type=str,
                        choices=VALID_NORMALIZE_METHODS,
                        default=DEFAULT_NORMALIZE_METHOD)
    parser.add_argument('-na', '--ignore_nas', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    return parser


def make_network_unweighted(n_df, wgt):
    """
    Make the network unweighted, by setting the weights on all the edges to the
    same value (1).

    Parameters:
        n_df (list): the data
        wgt (int): the weight column

    Returns:
        list: the modified data
    """
    return [n[:wgt] + [1] + n[wgt+1:] for n in n_df]


def make_network_undirected(n_df):
    """
    Make the network undirected; that is, the network should be symmetric, but
    only the edges in one direction are included.  So make the edges in the
    other direction explicit in the network. This assumes that the first two
    columns are the two nodes.

    Parameters:
        n_df (list): the data

    Returns:
        list: the modified data
    """

    return n_df + [[n[1], n[0]] + n[2:] for n in n_df]


def sort_network(n_df):
    """
    Sort the network.

    Parameters:
        n_df (list): the data

    Returns:
        list: the modified data
    """
    return sorted(n_df, reverse=True)


def drop_duplicates_by_type_or_node(n_df, n1, n2, typ):
    """
    Drop the duplicates in the network, by type or by node.

    For each set of "duplicate" edges, only the edge with the maximum weight
    will be kept.

    By type, the duplicates are where nd1, nd2, and typ are identical; by node,
    the duplicates are where nd1, and nd2 are identical.

    Parameters:
        n_df (list): the data
        n1 (int): the column for the firts node
        n2 (int): the column for the second node
        typ (int): the column for the type

    Returns:
        list: the modified data
    """
    # If n_df is sorted, this method will work, iterating through the
    # rows and only keeping the first row of a group of duplicate rows
    prev_nd1_val = None
    prev_nd2_val = None
    prev_type_val = None

    new_n_df = []

    for row in n_df:
        nd1_val = row[n1]
        nd2_val = row[n2]
        type_val = row[typ]
        nodes_differ = nd1_val != prev_nd1_val or nd2_val != prev_nd2_val
        type_differs = type_val != prev_type_val
        if (DROP_DUPLICATES_METHOD == 'node' and nodes_differ) or (nodes_differ or type_differs):
            new_n_df.append(row)
        prev_nd1_val = nd1_val
        prev_nd2_val = nd2_val
        prev_type_val = type_val

    return new_n_df


def normalize_network_by_type(n_df, typ, wgt):
    """
    Normalize the network.

    Currently the only normalization method implemented is by type.

    Parameters:
        n_df (list): the data
        typ (int): the type column
        wgt (int): the weight column

    Returns:
        list: the modified data
    """
    sums = collections.Counter()
    for i in n_df:
        sums[i[typ]] += i[wgt]

    return [i[:wgt] + ("{:.6g}".format(i[wgt]/sums[i[typ]]),) + i[wgt+1:] for i in n_df]


def upper_triangle(n_df, n1, n2):
    """Makes a (sparse) matrix upper triangular.
    """
    return [edge for edge in n_df if edge[n1] < edge[n2]]
