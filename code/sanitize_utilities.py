#!/usr/bin/env python3

#UNDOC
"""
.. codeauthor:: Charles Blatti <blatti@illinois.edu>
.. codeauthor:: Milt Epstein <mepstein@illinois.edu>

This script "sanitizes" a network file through a series of steps, some
of which are optional.

Each line, or row, in the network file represents an edge, and
contains four columns.  The four columns are the source and
destination nodes, the edge weight, and the edge type.

The original network file is specified via the -inet/--network_file
option, which is required.

Two output files are produced, the resulting "clean" four column
network file, and a file containing the names of the nodes in the
network.  The name of the clean four column network file is specified
via the -o/--output_file option, the name of the node name file via
the -onn/--output_file_node_names option.

The sanitization steps are:

1. If the node_map_file is specified, via the -inod/--node_map_file
option, the node names (columns 1 and 2) are mapped as specified in
that file.  (That file consists of two columns, with the original node
name in the second column and the mapped node name in the first.)

2. If the -unw/--make_unweighted option is specified, the edge weights
(column 3) are all set to the same value (currently 1).

3. If the -und/--make_undirected option is specified, then a reverse
copy (i.e., with the nodes switched) of each edge will be added to the
network specification.  This is basically interpreting the original
network specification as being symmetrical with only undirected edges
specified.  (This behavior can also be thought of as add_symmetrical
edges to the network.)

4. If DROP_DUPLICATES_METHOD is not None, then the specified
duplicates will be removed from the network specification.

5. If the -norm/--normalize option is specified, the edge weights will
be normalized by type (i.e., for each type, the sum of the weights of
all the edges of that type will be computed, and then each edge's
weight will be divided by the sum for its type).

(Currently the only normalize option is by type; other normalization
options may be added, in which case the -normm/--normalize_method
option will be used to specify it.  That option currently does not do
anything.)

Note: If the -na/--ignore_nas option is specified, then NA values in
the original network file will be interpreted literally rather than as
NaN.  (This was needed because NA was used as a node name in certain
network files.)

**Arguments**

.. csv-table::
    :header: flag,name,type,status,reqs.,description
    :widths: 5,20,5,20,10,40
    :delim: |

    -inet|--network_file|str|required||the input network file
    -inod|--node_map_file|str|optional, default: None||the input node map file
    -o|--output_file|str|optional, default: None||the output file for the cleaned edge file
    -onn|--output_file_node_names|str|optional, default: None||the output file for the node names
    -und|--make_undirected|bool|||whether to make the edges undirected
    -unw|--make_unweighted|bool|||whether to make the edges unweighted
    -norm|--normalize|bool|||whether to normalize the edges
    -normm|--normalize_method|str||choices=VALID_NORMALIZE_METHODS| \
        which normalization method to use (this is not currently used; the \
        only normalization method currently available is 'type')
    -na|--ignore_nas|bool|||whether to ignore NA's/NaN's in input data
"""


import argparse
import sys
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
    Parse the arguments.

    Parse the command line arguments/options using the argparse module
    and return the parsed arguments (as an argparse.Namespace object,
    as returned by argparse.parse_args()).

    Returns:
        argparse.Namespace: the parsed arguments
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


def make_network_unweighted(n_df, wgt): #NEW, UNDOC
    """
    Make the network unweighted, by setting the weights
    on all the edges to the same value.

    Parameters:
        n_df (pandas.DataFrame): the dataframe
        wgt (str): the weight column label

    Returns:
        pandas.DataFrame: the modified dataframe
    """
    return [n[:wgt] + [1] + n[wgt+1:] for n in n_df]


def make_network_undirected(n_df): #NEW, UNDOC
    """
    Make the network undirected, i.e., add symmetrical edges
    to the ones already there.

    Make the network undirected; that is, the network should be
    symmetric, but only the edges in one direction are included.  So
    make the edges in the other direction explicit in the network.

    Parameters:
        n_df (pandas.DataFrame): the dataframe
        args (argparse.Namespace): the parsed arguments

    Returns:
        pandas.DataFrame: the modified dataframe
    """

    return n_df + [[n[1], n[0]] + n[2:] for n in n_df]


def sort_network(n_df): #NEW, UNDOC
    """
    Sort the network.

    How the network is sorted depends on how duplicates are going to
    be dropped, as indicated by DROP_DUPLICATES_METHOD.  This will
    allow the appropriate drop_duplicates*() method to work.  If it's
    by 'node', then sort by nd1, nd2 (all string ascending), wgt
    (numeric descending); if it's by 'type', then sort by nd1, nd2,
    typ (all string ascending), wgt (numeric descending).  If it's
    'exact' or None, it doesn't matter which way it's sorted; sort the
    same as if it's 'type'.

    Parameters:
        n_df (pandas.DataFrame): the dataframe
        nd1 (str): the node 1 column label
        nd2 (str): the node 2 column label
        typ (str): the type column label
        wgt (str): the weight column label

    Returns:
        pandas.DataFrame: the modified dataframe
    """
    return sorted(n_df, reverse=True)


def drop_duplicates_by_type_or_node(n_df, n1, n2, typ): #NEW, UNDOC
    """
    Drop the duplicates in the network, by type or by node.

    For each set of "duplicate" edges, only the edge with the maximum
    weight will be kept.

    By type, the duplicates are where nd1, nd2, and typ are identical;
    by node, the duplicates are where nd1, and nd2 are identical.

    Parameters:
        n_df (pandas.DataFrame): the dataframe
        args (argparse.Namespace): the parsed arguments

    Returns:
        pandas.DataFrame: the modified dataframe
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


def normalize_network_by_type(n_df, typ, wgt): #NEW, UNDOC
    """
    Normalize the network.

    Currently the only normalization method implemented is by type.

    Parameters:
        n_df (pandas.DataFrame): the dataframe
        typ (str): the type column label
        wgt (str): the weight column label

    Returns:
        pandas.DataFrame: the modified dataframe
    """
    sums = collections.Counter()
    for i in n_df:
        sums[i[typ]] += i[wgt]

    return [i[:wgt] + ("{:.6g}".format(i[wgt]/sums[i[typ]]),) + i[wgt+1:] for i in n_df]
