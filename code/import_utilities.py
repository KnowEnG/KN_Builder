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


def import_file(file_name, table, ld_cmd='', dup_cmd='', args=cf.config_args()):
    """Imports the provided  file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it uses the provided behavior to handle.

    Args:
        file_name (str): path to the file to be imported
        table (str): name of the permanent table to import to
        ld_cmd (str): optional additional command for loading data
        dup_cmd (str): command for handling duplicates
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    tmptable = os.path.splitext(os.path.basename(file_name))[0].replace('.', '_')
    print('Creating temporary table ' + tmptable)
    db.create_temp_table(tmptable, 'LIKE ' + table)
    print('Loading data into temporary table ' + tmptable)
    db.load_data(file_name, tmptable, ld_cmd)
    print('Inserting data from ' + tmptable + ' into ' + table)
    cmd = 'SELECT * FROM ' + tmptable
    if dup_cmd:
        cmd += ' ON DUPLICATE KEY UPDATE ' + dup_cmd.format(tmptable)
        db.insert(table, cmd)
    else:
        db.replace(table, cmd)
    db.drop_table(tmptable)
    db.close()

def import_filemeta(version_dict, args=cf.config_args()):
    """Imports the provided version_dict into the KnowEnG MySQL database.

    Loads the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    values = [version_dict["source"] + '.' + version_dict["alias"],
              version_dict["remote_url"], version_dict["remote_date"],
              version_dict["remote_version"], version_dict["remote_size"],
              'CURRENT_TIMESTAMP', version_dict["local_file_name"], 'NULL']
    for i in range(0, len(values)):
        val = values[i]
        if val == 'CURRENT_TIMESTAMP' or val == 'NULL':
            continue
        elif type(val) is str:
            values[i] = '"' + val + '"'
        else:
            values[i] = str(val)
    values = [str(i) for i in values]
    cmd = 'VALUES( ' + ','.join(values) + ')'
    db.replace('raw_file', cmd)

def update_filemeta(version_dict, args=cf.config_args()):
    """Updates the provided filemeta into the KnowEnG MySQL database.

    Updates the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args: command line and default arguements

    Returns:
    """
    db = mu.get_database('KnowNet', args)
    values = [version_dict["source"] + '.' + version_dict["alias"],
              version_dict["remote_url"], version_dict["remote_date"],
              version_dict["remote_version"], version_dict["remote_size"],
              'CURRENT_TIMESTAMP', version_dict["local_file_name"],
              version_dict["checksum"]]
    for i in range(0, len(values)):
        val = values[i]
        if val == 'CURRENT_TIMESTAMP' or val == 'NULL':
            continue
        elif type(val) is str:
            values[i] = '"' + val + '"'
        else:
            values[i] = str(val)
    values = [str(i) for i in values]
    cmd = 'VALUES( ' + ','.join(values) + ')'
    db.replace('raw_file', cmd)

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
    imports = ['node_meta', 'edge2line', 'edge', 'edge_meta']
    uedge_cmd  = ('edge.weight = IF(edge.weight > {0}.weight, edge.weight, '
                    '{0}.weight)')
    for table in imports:
        ld_cmd = ''
        dup_cmd = ''
        if table == 'edge':
            filename = edgefile
            dup_cmd = uedge_cmd
        else:
            filename = edgefile.replace('conv', table)
        if not os.path.isfile(filename):
            continue
        if table == 'node_meta':
            ld_cmd = '(@dummy, node_id, info_type, info_desc)'
        import_file(filename, table, ld_cmd, dup_cmd, args)


def import_nodemeta(nmfile, args=cf.config_args()):
    """Imports the provided node_meta file and any corresponding meta files into
    the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        nm (str): path to the file to be imported
        args: command line and default arguements

    Returns:
    """
    table = 'node_meta'
    dup_cmd = ''
    ld_cmd = '(@dummy, node_id, info_type, info_desc)'
    import_file(nmfile, table, ld_cmd, dup_cmd, args)

def import_pnode(filename, args=cf.config_args()):
    """Imports the provided property node file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        filename (str): path to the file to be imported
        args: command line and default arguements

    Returns:
    """
    ld_cmd = '(node_id, n_alias) SET n_type_id=2'
    dup_cmd = ''
    table = 'node'
    import_file(filename, table, ld_cmd, dup_cmd, args)
