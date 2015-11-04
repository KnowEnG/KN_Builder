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


def import_file(file_name, table, ld_cmd='', dup_cmd='IGNORE', args=cf.config_args()):
    """Imports the provided  file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it uses the provided behavior to handle.

    Args:
        file_name (str): path to the file to be imported
        table (str): name of the permanent table to import to
        ld_cmd (str): optional additional command for loading data
        dup_cmd (str): command for handling duplicates, by default it ignores
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    tmptable = os.path.splitext(os.path.basename(file_name))[0].replace('.', '-')
    db.create_temp_table(tmptable, 'LIKE ' + table)
    db.load_data(file_name, table, ld_cmd)
    cmd = 'SELECT * FROM ' + tmptable + ' ON DUPLICATE KEY ' + dup_cmd
    db.insert(table, cmd)

def import_edgefile(edgefile, args=cf.config_args()):
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
    imports = ['node_meta', 'edge2line', 'edge', 'edge_meta']
    for table in imports:
        ld_cmd = ''
        dup_cmd = ''
        if table == 'edge':
            filename = edgefile
            dup_cmd = ('UPDATE weight = IF(weight > VALUES(weight), weight, '
                       'VALUES(weight))')
        else:
            filename = edgefile.replace('conv', table)
        if not os.path.isfile(filename):
            continue
        if table == 'node_meta':
            ld_cmd = '(@dummy, column1, column2, column3)'
        import_file(filename, table, ld_cmd, dup_cmd, args)

def import_nodefile(nodefile, n_type_id, args=cf.config_args()):
    """Imports the provided node file and into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        nodefile (str): path to the file to be imported
        args: command line and default arguements

    Returns:
    """
    ld_cmd = '(column1, column2) SET column3 = ' + str(n_type_id)
    dup_cmd = ''
    import_file(nodefile, 'node', ld_cmd, dup_cmd, args)
