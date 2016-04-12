"""Utiliites for importing edge, edge_meta, and node_meta into the KnowEnG
MySQL datatbase.

Contains module functions::

    import_file(file_name, table, ld_cmd='', dup_cmd='', args=None)
    import_filemeta(version_dict, args=None)
    update_filemeta(version_dict, args=None)
    import_edge(edgefile, args=None)
    import_nodemeta(nmfile, args=None)
    import_pnode(filename, args=None)

"""

import config_utilities as cf
import mysql_utilities as mu
import json
import os

@profile
def import_file(file_name, table, ld_cmd='', dup_cmd='', args=None):
    """Imports the provided  file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it uses the provided behavior to handle. If no
    behavior is provided, it replaces into the table.

    Args:
        file_name (str): path to the file to be imported
        table (str): name of the permanent table to import to
        ld_cmd (str): optional additional command for loading data
        dup_cmd (str): command for handling duplicates
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    table_cmds = {'node_meta': 'node_meta.node_id = node_meta.node_id',
                'node': 'node.node_id = node.node_id',
                'raw_line' : 'raw_line.file_id = raw_line.file_id',
                'edge2line': 'edge2line.edge_hash = edge2line.edge_hash',
                'edge_meta': 'edge_meta.edge_hash = edge_meta.edge_hash',
                'edge': ('edge.weight = IF(edge.weight > {0}.weight, edge.weight, '
                    '{0}.weight)'),
                'status': ('status.weight = IF(status.weight > {0}.weight, status.weight, '
                    '{0}.weight)')}
    if not dup_cmd and table in table_cmds:
        dup_cmd = table_cmds[table]
    db = mu.get_database('KnowNet', args)
    tmptable = os.path.splitext(os.path.basename(file_name))[0].replace('.', '_')
    tmptable = cf.pretty_name(tmptable, len(tmptable)).replace('-', '_')[:64]
    print('Creating temporary table ' + tmptable)
    db.create_temp_table(tmptable, 'LIKE ' + table)
    print('Loading data into temporary table ' + tmptable)
    db.load_data(file_name, tmptable, ld_cmd)
    print('Inserting data from ' + tmptable + ' into ' + table)
    cmd = 'SELECT * FROM ' + tmptable
    if dup_cmd:
        cmd += ' ON DUPLICATE KEY UPDATE ' + dup_cmd.format(tmptable)
        db.start_transaction(level='READ COMMITTED')
        db.insert(table, cmd)
    else:
        db.start_transaction(level='READ COMMITTED')
        db.replace(table, cmd)
    db.drop_table(tmptable)
    db.close()

def import_filemeta(version_dict, args=None):
    """Imports the provided version_dict into the KnowEnG MySQL database.

    Loads the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
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

def update_filemeta(version_dict, args=None):
    """Updates the provided filemeta into the KnowEnG MySQL database.

    Updates the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
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

def import_edge(edgefile, args=None):
    """Imports the provided edge file and any corresponding meta files into
    the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        edgefile (str): path to the file to be imported
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    imports = ['node', 'node_meta', 'edge2line', 'edge', 'edge_meta']
    #uedge_cmd  = ('edge.weight = IF(edge.weight > {0}.weight, edge.weight, '
    #                '{0}.weight)')
    for table in imports:
        ld_cmd = ''
        dup_cmd = ''
        if table == 'edge':
            filename = edgefile
        else:
            filename = edgefile.replace('conv', table)
        ufile = filename.replace(table, 'unique_' + table)
        if os.path.isfile(ufile):
            filename = ufile
        if not os.path.isfile(filename):
            continue
        import_file(filename, table, ld_cmd, dup_cmd, args)

def import_status(statusfile, args=None):
    """Imports the provided status file and any corresponding meta files into
    the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        status (str): path to the file to be imported
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    imports = ['node', 'node_meta', 'edge2line', 'status', 'edge_meta']
    for table in imports:
        ld_cmd = ''
        dup_cmd = ''
        if table == 'status':
            filename = statusfile
        else:
            filename = statusfile.replace('status', table)
        ufile = filename.replace(table, 'unique_' + table)
        if os.path.isfile(ufile):
            filename = ufile
        if not os.path.isfile(filename):
            continue
        import_file(filename, table, ld_cmd, dup_cmd, args)

def import_nodemeta(nmfile, args=None):
    """Imports the provided node_meta file and any corresponding meta files into
    the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        nmfile (str): path to the file to be imported
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    table = 'node_meta'
    dup_cmd = 'node_meta.node_id = node_meta.node_id'
    ld_cmd = ''
    import_file(nmfile, table, ld_cmd, dup_cmd, args)

def import_pnode(filename, args=None):
    """Imports the provided property node file into the KnowEnG MySQL database.

    Loads the data into a temporary table in MySQL. It then queries from the
    temporary table into the corresponding permanent table. If a duplication
    occurs during the query, it updates to the maximum edge score if it is an
    edge file, and ignores if it is metadata.

    Args:
        filename (str): path to the file to be imported
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    ld_cmd = '(node_id, n_alias) SET n_type_id=2'
    dup_cmd = 'node.node_id = node.node_id'
    table = 'node'
    import_file(filename, table, ld_cmd, dup_cmd, args)
