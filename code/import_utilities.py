"""Utiliites for importing edge, edge_meta, and node_meta into the KnowEnG
MySQL datatbase.

Classes:


Functions:


Variables:
"""

import config_utilities as cf
import mysql_utilities as mu
import json
import os


def import_file(infile, table, args=cf.config_args()):
    """Imports the provided  file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it uses the provided behavior to handle.

    Args:
        file (str): path to the file to be imported
        table (str): name of the permanent table to import to
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    tmptable = os.path.splitext(os.path.basename(edgefile))[0].replace('.', '-')
    db.create_temp_table(tmptable, 'LIKE ' + table)
    
    

def import_edge(edgefile, args=cf.config_args()):
    """Imports the provided edge file and any corresponding meta files into
    the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        edgefile (str): path to the file to be imported
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    tmptable = os.path.splitext(os.path.basename(edgefile))[0].replace('.', '-')
    db.create_temp_table(tmptable, 'LIKE edge')
    

