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

import os
import csv
import subprocess
from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as mu
import redis_utilities as ru

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
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    print('Inserting data from into ' + table)
    db.load_data(file_name, table, ld_cmd)
    db.close()

def import_file_nokeys(file_name, table, ld_cmd='', args=None):
    """Imports the provided  file into the KnowEnG MySQL database using optimal
    settings.

    Starts a transaction and changes some MySQL settings for optimization, which
    disables the keys. It then loads the data into the provided table in MySQL.
    Note that the keys are not re-enabled after import. To do this call
    enable_keys(args).

    Args:
        file_name (str): path to the file to be imported
        table (str): name of the permanent table to import to
        ld_cmd (str): optional additional command for loading data
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    print('Inserting data from into ' + table)
    db.disable_keys()
    db.load_data(file_name, table, ld_cmd)
    db.close()

def enable_keys(args=None):
    """Imports the provided  file into the KnowEnG MySQL database using optimal
    settings.

    Starts a transaction and changes some MySQL settings for optimization, which
    disables the keys. It then loads the data into the provided table in MySQL.
    Note that the keys are not re-enabled after import. To do this call
    mysql_utilities.get_database('KnowNet', args).enable_keys().

    Args:
        file_name (str): path to the file to be imported
        table (str): name of the permanent table to import to
        ld_cmd (str): optional additional command for loading data
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    db.enable_keys()
    db.close()

def import_filemeta(version_dict, args=None):
    """Imports the provided version_dict into the KnowEnG MySQL database.

    Loads the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    values = [version_dict["source"] + '.' + version_dict["alias"],
              version_dict["remote_url"], version_dict["remote_date"],
              version_dict["remote_version"], version_dict["remote_size"],
              version_dict["source_url"], version_dict["image"], version_dict["reference"],
              version_dict["pmid"], version_dict["license"],
              'CURRENT_TIMESTAMP', version_dict["local_file_name"], 'NULL']
    cmd = 'VALUES( ' + ','.join('%s' for i in values) + ')'
    db.replace_safe('raw_file', cmd, values)
    db.close()

def update_filemeta(version_dict, args=None):
    """Updates the provided filemeta into the KnowEnG MySQL database.

    Updates the data from an version dictionary into the raw_file table.

    Args:
        version_dict (dict): version dictionary describing a downloaded file
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    values = [version_dict["source"] + '.' + version_dict["alias"],
              version_dict["remote_url"], version_dict["remote_date"],
              version_dict["remote_version"], version_dict["remote_size"],
              version_dict["source_url"], version_dict["image"], version_dict["reference"], version_dict["pmid"], version_dict["license"],
              'CURRENT_TIMESTAMP', version_dict["local_file_name"],
              version_dict["checksum"]]
    cmd = 'VALUES( ' + ','.join('%s' for i in values) + ')'
    db.replace_safe('raw_file', cmd, values)
    db.close()

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
        args = cf.config_args()
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
        ufile = filename.replace(table, 'unique.' + table)
        if os.path.isfile(ufile):
            filename = ufile
        if not os.path.isfile(filename):
            continue
        import_file(filename, table, ld_cmd, dup_cmd, args)

def import_production_edges(args=None):
    """Query production edges from status table into the edge table.

    Queries the KnowNet status table and copies all distinct production edges
    to the edge table. If a duplication occurs during the query, it updates to
    the maximum edge score and keeps the edge hash for that edge.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    """

    if args is None:
        args = cf.config_args()
    db = mu.get_database('KnowNet', args)
    cmd = ('SELECT DISTINCT n1_id, n2_id, et_name, weight, edge_hash '
           'FROM KnowNet.status WHERE status.status="production" '
           'ON DUPLICATE KEY UPDATE edge.weight = '
           'IF(edge.weight > status.weight, edge.weight, status.weight)')
    tablename = 'KnowNet.edge'
    db.insert(tablename, cmd)

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
        args = cf.config_args()
    imports = ['node', 'node_meta', 'edge2line', 'status', 'edge_meta']
    for table in imports:
        ld_cmd = ''
        dup_cmd = ''
        if table == 'status':
            filename = statusfile
        else:
            filename = statusfile.replace('status', table)
        ufile = filename.replace(table, 'unique.' + table)
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
        args = cf.config_args()
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
        args = cf.config_args()
    ld_cmd = '(node_id, n_alias) SET n_type="Property"'
    dup_cmd = 'node.node_id = node.node_id'
    table = 'node'
    import_file(filename, table, ld_cmd, dup_cmd, args)

def merge(merge_key, args):
    """Uses sort to merge and unique the already sorted files of the table type
    and stores the results into outfile.

    This takes a table type (one of: node, node_meta, edge2line, status, or
    edge_meta) and merges them using the unix sort command while removing any
    duplicate elements.

    Args:
        merge_key (str): table type (one of: node, node_meta, edge2line, status,
            edge, or edge_meta)
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    if args.storage_dir:
        searchpath = os.path.join(args.storage_dir, args.data_path)
    else:
        searchpath = os.path.join(args.working_dir, args.data_path)
    outpath = os.path.join(args.working_dir, args.data_path)
    if merge_key == 'edge':
        outfile = os.path.join(outpath, 'unique-sort.' + merge_key + '.txt')
    else:
        outfile = os.path.join(outpath, 'unique.' + merge_key + '.txt')
    searchpath = os.path.join(searchpath, '*', '*', '*')
    with open(outfile, 'w') as out:
        cmd1 = ['find', searchpath, '-type', 'f',
                '-name', '*.unique.'+merge_key+'.*', '-print0']
        temppath = os.path.join(outpath, 'tmp')
        if not os.path.isdir(temppath):
            os.makedirs(temppath)
        cmd2 = ['xargs', '-0', 'sort', '-mu', '-T', temppath]
        print(' '.join(cmd1))
        print(' '.join(cmd2))
        p1 = subprocess.Popen(' '.join(cmd1), stdout=subprocess.PIPE, shell=True)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()

    if merge_key != 'edge':
        return outfile

    us_file = outfile
    ud_file = os.path.join(outpath, 'unique-dup.edge.txt')
    ue_file = os.path.join(outpath, 'unique.edge.txt')
    with open(us_file, 'r') as infile, \
        open(ud_file, 'w') as edge:
        reader = csv.reader(infile, delimiter='\t')
        writer = csv.writer(edge, delimiter='\t', lineterminator='\n')
        prev = False
        for line in reader:
            line = line[1:] + [line[0]]
            e_chksum = line[4]
            weight = line[3]
            if not prev:
                prev = line
            if e_chksum != prev[4]:
                writer.writerow(prev)
                prev = line
            elif float(weight) > float(prev[3]):
                prev = line
        if prev:
            writer.writerow(prev)
    os.remove(us_file)
    with open(ue_file, 'w') as out:
        cmd1 = ['cat', ud_file]
        temppath = os.path.join(outpath, 'tmp')
        if not os.path.isdir(temppath):
            os.makedirs(temppath)
        cmd2 = ['sort', '-u', '-T', temppath]
        print(' '.join(cmd1))
        print(' '.join(cmd2))
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()
    os.remove(ud_file)
    return ue_file


def merge_logs(args):
    """Merge all log files into a single file that contains all the information about the run.
    """

    if args.storage_dir:
        searchpath = os.path.join(args.storage_dir)
    else:
        searchpath = os.path.join(args.working_dir)
    searchfile = os.path.join(searchpath, '../logs_*/*.log')
    outpath = os.path.join(args.working_dir, args.data_path)
    outfile = os.path.join(outpath, 'unique.log.txt')
    with open(outfile, 'w') as out:
        cmd1 = ["""awk -F'\t' -v OFS='\t' '$1 == "run info" {$1 = FILENAME; print}'""", searchfile]
        cmd2 = ['cut', '-f2-', '-d\t']
        print(' '.join(cmd1))
        print(' '.join(cmd2))
        p1 = subprocess.Popen(' '.join(cmd1), stdout=subprocess.PIPE, shell=True)
        subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out).communicate()
    return outfile


def main_parse_args():
    """Processes command line arguments.

    Expects one positional argument (status_file) and number of optional
    arguments. If arguments are missing, supplies default values.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('importfile', help='import file produced from map step, \
                        or merged files, and must contain the table name e.g. \
                        kegg/ath/kegg.ath.unique.status.1.txt or \
                        unique.status.txt')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

def main():
    """Imports according to the given arguments.
    """
    args = main_parse_args()
    merge_keys = ['node', 'node_meta', 'edge2line', 'status', 'edge', \
                  'edge_meta', 'raw_line', 'table', 'log']
    if args.importfile == 'log':
        args.importfile = merge_logs(args)
    elif args.importfile in merge_keys:
        args.importfile = merge(args.importfile, args)
    table = ''
    ld_cmd = ''
    dup_cmd = ''
    for key in args.importfile.split('.'):
        if key in merge_keys:
            table = key
            break
    if not table:
        raise ValueError("ERROR: 'importfile' must contain one of "+\
                         ','.join(merge_keys))
    import_file(args.importfile, table, ld_cmd, dup_cmd, args)
    if table == 'node_meta':
        filename = args.importfile.replace("node_meta", "node_meta_table")
        mu.get_database("KnowNet", args).dump_table(table, filename)
        ru.import_node_meta(filename, args)

if __name__ == "__main__":
    main()
