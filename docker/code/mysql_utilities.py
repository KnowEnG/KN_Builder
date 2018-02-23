#!/usr/bin/env python3

"""Utiliites for interacting with the KnowEnG MySQL db through python.

Contains the class MySQL which provides functionality for interacting with
MySQL database

Contains module functions::

    combine_tables(alias, args=None)
    create_dictionary(results)
    import_nodes(version_dict, args=None)
    query_all_mappings(version_dict, args=None)
    create_mapping_dicts(version_dict, args=None)
    get_database(db=None, args=None)
    get_insert_cmd(step)
    import_ensembl(alias, args=None)
"""
import os
import json
import subprocess
import shutil
from argparse import ArgumentParser
import config_utilities as cf
import mysql.connector as sql

def deploy_container(args=None):
    """Deplays a container with marathon running MySQL using the specified
    args.

    This replaces the placeholder args in the json describing how to deploy a
    container running mysql with those supplied in the users arguements.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    deploy_dir = os.path.join(args.working_dir, args.logs_path, 'marathon_jobs')
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)
    template_job = os.path.join(args.working_dir, args.code_path, 'dockerfiles', 'marathon',
                                'mysql.json')
    with open(template_job, 'r') as infile:
        deploy_dict = json.load(infile)
    deploy_dict["id"] = os.path.basename(args.mysql_dir)
    deploy_dict["cpus"] = float(args.mysql_cpu)
    deploy_dict["mem"] = int(args.mysql_mem)
    if args.mysql_curl:
        deploy_dict["constraints"] = [["hostname", "CLUSTER", args.mysql_curl]]
    else:
        deploy_dict["constraints"] = []
    conf_template = os.path.join(args.working_dir, args.code_path, 'mysql', args.mysql_conf)
    if args.storage_dir:
        mysql_dir = os.path.join(args.storage_dir, args.data_path, 'mysql')
    else:
        mysql_dir = os.path.join(args.working_dir, args.data_path, 'mysql')
    conf_path = os.path.join(mysql_dir, args.mysql_conf)
    if not os.path.exists(conf_path):
        os.makedirs(conf_path)
    os.chmod(os.path.dirname(mysql_dir), 0o777)
    shutil.copy(os.path.join(conf_template, 'my.cnf'), os.path.join(conf_path, 'my.cnf'))
    with open(os.path.join(conf_path, 'password'), 'w') as f:
        f.write(args.mysql_pass)
    deploy_dict["container"]["volumes"][0]["hostPath"] = args.mysql_dir
    deploy_dict["container"]["volumes"][1]["hostPath"] = conf_path
    deploy_dict["container"]["docker"]["parameters"][0]["value"] = \
                    "MYSQL_ROOT_PASSWORD=KnowEnG"
    out_path = os.path.join(deploy_dir, "p1mysql-" + args.mysql_port +'.json')
    with open(out_path, 'w') as outfile:
        outfile.write(json.dumps(deploy_dict))
    job = 'curl -X POST -H "Content-type: application/json" ' + args.marathon + " -d '"
    job += json.dumps(deploy_dict) + "'"
    if not args.test_mode:
        try:
            subprocess.check_output(job, shell=True)
        except subprocess.CalledProcessError as ex1:
            print(ex1.output)
    else:
        print(job)


def combine_tables(alias, args=None):
    """Combine all of the data imported from ensembl for the provided alias
    into a single database.

    This combines the imported tables into a single table knownet_mappings with
    information from genes, transcripts, and translations. It then merges this
    table into the KnowNet database for use in gene identifier mapping.

    Args:
        alias (str): An alias defined in ensembl.aliases.
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    alias_db = 'ensembl_' + alias
    combined_db = 'KnowNet'
    combined_table = alias + '_mappings'
    all_table = 'all_mappings'
    steps = ['transcript', 'translation', 'transcript2stable',
             'translation2stable']
    db = MySQL(alias_db, args)
    db.create_table(combined_table, get_insert_cmd('gene'))
    for step in steps:
        db.insert(combined_table, get_insert_cmd(step))
    db.use_db(combined_db)
    cmd = ("SELECT *, db_display_name AS species FROM " + alias_db + '.' +
           alias + "_mappings WHERE 1=2")
    db.create_table(all_table, cmd)
    cmd = ("SELECT UCASE(dbprimary_acc) as dbprimary_acc, "
           "UCASE(display_label) AS display_label, "
           "UCASE(db_name) AS db_name, priority, "
           "UCASE(db_display_name) AS db_display_name, "
           "UCASE(stable_id) AS stable_id, '" + alias + "' AS species FROM " +
           alias_db + '.' + alias + "_mappings")
    db.insert(all_table, cmd)
    db.close()

def create_dictionary(results):
    """Creates a dictionary from a MySQL fetched results.

    This returns a dictionary from the MySQL results after a query from the DB.
    It assumes there are two columns in the results and reads through all of
    the results, making them into a dictionary.

    Args:
        results (list): a list of the results returned from a MySQL query

    Returns:
        dict: dictionary with first column as key and second as values
    """
    map_dict = dict()
    for (raw, mapped) in results:
        map_dict[str(raw)] = str(mapped)
    return map_dict

def import_nodes(version_dict, args=None):
    """Imports the gene nodes into the KnowNet nodes and node_species tables.

    Queries the imported ensembl nodes and uses the stable ids as nodes for
    the KnowNet nodes table and uses the taxid to create the corresponding
    node_species table.

    Args:
        version_dict (dict): the version dictionary describing the
            source:alias
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    alias = version_dict['alias']
    taxid = version_dict['alias_info'].split('::')[0]
    alias_db = 'ensembl_' + alias
    db = MySQL(alias_db, args)
    cmd = ("SELECT DISTINCT UCASE(gene.stable_id) AS node_id, "
           "SUBSTRING(gene.description, 1, 512) AS n_alias, "
           "'Gene' AS n_type_id "
           "FROM gene "
           "ON DUPLICATE KEY UPDATE node_id=node_id")
    tablename = 'KnowNet.node'
    db.insert(tablename, cmd)
    cmd = ("SELECT DISTINCT UCASE(gene.stable_id) AS node_id, " + taxid +
           " AS taxon FROM gene ON DUPLICATE KEY UPDATE node_id=node_id")
    tablename = 'KnowNet.node_species'
    db.insert(tablename, cmd)
    cmd = ("SELECT DISTINCT UCASE(gene.stable_id) AS node_id, "
           "'biotype' AS info_type, "
           "gene.biotype AS info_desc "
           "FROM gene "
           "ON DUPLICATE KEY UPDATE node_id=node_id")
    tablename = 'KnowNet.node_meta'
    db.insert(tablename, cmd)
    cmd = ("SELECT DISTINCT UCASE(gene.stable_id) AS node_id, 'taxid' AS info_type, " + taxid +
           " AS info_desc FROM gene ON DUPLICATE KEY UPDATE node_id=node_id")
    tablename = 'KnowNet.node_meta'
    db.insert(tablename, cmd)
    cmd = ("SELECT DISTINCT UCASE(gene.stable_id) AS node_id, "
           "gene.description AS n_alias, "
           "'Gene' AS n_type_id "
           "FROM gene")
    return db.run(cmd)

def query_all_mappings(version_dict, args=None):
    """Creates the all mappings dictionary for the provided alias.

    Produces a dictionary of ensembl stable mappings and the all unique mappings
    the provided alias. It then saves them as json objects to
    file.

    Args:
        version_dict (dict): the version dictionary describing the
            source:alias
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    alias = version_dict['alias']
    taxid = version_dict['alias_info']
    database = 'ensembl_' + alias
    table = alias + '_mappings'
    map_dir = os.path.join(args.data_path, cf.DEFAULT_MAP_PATH)
    if os.path.isdir(args.working_dir):
        map_dir = os.path.join(args.working_dir, map_dir)
    if not os.path.isdir(map_dir):
        os.mkdir(map_dir)
    db = MySQL(database, args)
    cmd = "WHERE db_name='ENS_LRG_GENE'"
    results = db.query_distinct('dbprimary_acc, stable_id', table, cmd)
    lrg_dict = create_dictionary(results)
    results = db.query_distinct('stable_id, stable_id', table)
    map_dict = dict()
    for (raw, mapped) in results:
        if str(raw) in lrg_dict:
            mapped = lrg_dict[str(raw)]
        if str(mapped) in lrg_dict:
            mapped = lrg_dict[str(mapped)]
        map_dict[taxid + '::ENSEMBL_STABLE_ID::' + str(raw)] = str(mapped)
    results = db.query_distinct('display_label AS dbprimary_acc, db_name, stable_id',
                                table)
    results.extend(db.query_distinct('dbprimary_acc, db_name, stable_id',
                                     table))
    for (raw, hint, mapped) in results:
        if str(raw) in lrg_dict:
            mapped = lrg_dict[str(raw)]
        if str(mapped) in lrg_dict:
            mapped = lrg_dict[str(mapped)]
        map_dict['::'.join([taxid, str(hint), str(raw)])] = str(mapped)
    with open(os.path.join(map_dir, alias + '_all.json'), 'w') as outfile:
        json.dump(map_dict, outfile, indent=4)

def create_mapping_dicts(version_dict, args=None):
    """Creates the mapping dictionaries for the provided alias.

    Produces the ensembl stable mappings dictionary and the all unique mappings
    dictionary for the provided alias. It then saves them as json objects to
    file.

    Args:
        version_dict (dict): the version dictionary describing the
            source:alias
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    alias = version_dict['alias']
    taxid = version_dict['alias_info']
    database = 'KnowNet'
    table = 'all_mappings'
    cmd = "WHERE species='" + alias + "'"
    map_dir = os.path.join(args.data_path, cf.DEFAULT_MAP_PATH)
    if os.path.isdir(args.working_dir):
        map_dir = os.path.join(args.working_dir, map_dir)
    if not os.path.isdir(map_dir):
        os.mkdir(map_dir)
    db = MySQL(database, args)
    results = db.query_distinct('stable_id, stable_id', table, cmd)
    with open(os.path.join(map_dir, alias + '_stable.json'), 'w') as outfile:
        map_dict = create_dictionary(results)
        json.dump(map_dict, outfile, indent=4)
    results = db.query_distinct('display_label AS dbprimary_acc, stable_id',
                                table, cmd)
    results.extend(db.query_distinct('dbprimary_acc, stable_id', table, cmd))
    cmd += " AND db_name='ENS_LRG_gene'"
    results.extend(db.query_distinct('dbprimary_acc, stable_id', table, cmd))
    with open(os.path.join(map_dir, alias + '_unique.json'), 'w') as outfile:
        map_dict = create_dictionary(results)
        json.dump(map_dict, outfile, indent=4)

def get_database(db=None, args=None):
    """Returns an object of the MySQL class.

    This returns an object of the MySQL class to allow access to its functions
    if the module is imported.

    Args:
        db (str): optional db to connect to
        args (Namespace): args as populated namespace or 'None' for defaults

    Returns:
        MySQL: a source class object
    """
    if args is None:
        args = cf.config_args()
    return MySQL(db, args)

def create_KnowNet(args=None):
    """Returns an object of the MySQL class with KnowNet db.

    This returns an object of the MySQL class to allow access to its functions
    if the module is imported.

    Args:
        db (str): optional db to connect to
        args (Namespace): args as populated namespace or 'None' for defaults

    Returns:
        MySQL: a source class object
    """
    if args is None:
        args = cf.config_args()
    db = MySQL(None, args)
    db.init_knownet()
    return db

def get_insert_cmd(step):
    """Returns the command to be used with an insert for the provided step.

    This takes a predefined step to determine which type of insert is being
    performed during the production of the knownet_mappings combined tables.
    Based off of this step, it returns a MySQL command to be used with an
    INSERT INTO statement.

    Args:
        step (str): the step indicating the step during the production of the
            combined knownet_mapping tables

    Returns:
        str: the command to be used with an INSERT INTO statement at this step
    """
    if step == 'gene':
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, xref.display_label, "
               "external_db.db_name, external_db.priority, "
               "external_db.db_display_name, gene.stable_id "
               "FROM xref INNER JOIN external_db "
               "ON xref.external_db_id = external_db.external_db_id "
               "INNER JOIN object_xref "
               "ON xref.xref_id = object_xref.xref_id "
               "INNER JOIN gene "
               "ON object_xref.ensembl_id = gene.gene_id "
               "WHERE object_xref.ensembl_object_type = 'Gene'")
    elif step == 'transcript':
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, xref.display_label, "
               "external_db.db_name, external_db.priority, "
               "external_db.db_display_name, gene.stable_id "
               "FROM xref INNER JOIN external_db "
               "ON xref.external_db_id = external_db.external_db_id "
               "INNER JOIN object_xref "
               "ON xref.xref_id = object_xref.xref_id "
               "INNER JOIN transcript "
               "ON object_xref.ensembl_id = transcript.transcript_id "
               "INNER JOIN gene "
               "ON transcript.gene_id = gene.gene_id "
               "WHERE object_xref.ensembl_object_type = 'Transcript'")
    elif step == 'translation':
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, xref.display_label, "
               "external_db.db_name, external_db.priority, "
               "external_db.db_display_name, gene.stable_id "
               "FROM xref INNER JOIN external_db "
               "ON xref.external_db_id = external_db.external_db_id "
               "INNER JOIN object_xref "
               "ON xref.xref_id = object_xref.xref_id "
               "INNER JOIN translation "
               "ON object_xref.ensembl_id = translation.translation_id "
               "INNER JOIN transcript "
               "ON translation.transcript_id = transcript.transcript_id "
               "INNER JOIN gene "
               "ON transcript.gene_id = gene.gene_id "
               "WHERE object_xref.ensembl_object_type = 'Translation'")
    elif step == 'transcript2stable':
        cmd = ("SELECT DISTINCT transcript.stable_id AS dbprimary_acc, "
               "transcript.stable_id AS display_label, "
               "'ensembl' AS db_name, "
               "1000 AS priority, "
               "'ensembl' AS db_display_name, "
               "gene.stable_id "
               "FROM transcript "
               "INNER JOIN gene "
               "ON transcript.gene_id = gene.gene_id")
    elif step == 'translation2stable':
        cmd = ("SELECT DISTINCT translation.stable_id AS dbprimary_acc, "
               "translation.stable_id AS display_label, "
               "'ensembl' AS db_name, "
               "1000 AS priority, "
               "'ensembl' AS db_display_name, "
               "gene.stable_id "
               "FROM translation "
               "INNER JOIN transcript "
               "ON translation.transcript_id = transcript.transcript_id "
               "INNER JOIN gene "
               "ON transcript.gene_id = gene.gene_id")
    else:
        cmd = ''
    return cmd

def import_ensembl(alias, args=None):
    """Imports the ensembl data for the provided alias into the KnowEnG
    database.

    This produces the local copy of the fetched ensembl database for alias.
    It drops the existing database, creates a new database, imports the
    relevant ensembl sql schema, and imports the table.

    Args:
        alias (str): An alias defined in ensembl.aliases.
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    database = 'ensembl_' + alias
    db = MySQL(None, args)
    db.init_knownet()
    db.drop_db(database)
    db.import_schema(database, 'schema.sql')
    db.import_table(database, '*.txt')
    db.close()

def get_file_meta(file_id, args=None):
    """Returns the metadata for the provided file_id if it exists.

    This returns the metadata for the provided file_id (in the format of
    "source.alias") present locally in the MySQL database from a previous run
    of the pipeline. It formats this output as a dicionary, which will always
    contain the following keys:
    'file_id' (str):        "source.alias" which is the key \
                            used in SQL raw_file table
    'file_exists' (bool):   boolean if the file with the above file_id \
                            exists in the SQL raw_file table
    and will additionally contain the following keys if file_exists is True:
    'size' (int):           size of file in bytes
    'date' (float):         time of last modification time of file in \
                            seconds since the epoch
    'version' (str):        the remote version of the source

    Args:
        file_id (str):  The file_id for the raw_file in the format of \
                        "source.alias"

    Returns:
        dict: The file_meta information for a given source alias.
    """
    if args is None:
        args = cf.config_args()
    file_meta = {'file_id':file_id}
    db = get_database('KnowNet', args)
    results = db.query_distinct('remote_date, remote_size, remote_version',
                                'raw_file', 'WHERE file_id="'+file_id+'"')
    if not results:
        file_meta['file_exists'] = False
    else:
        file_meta['file_exists'] = True
        file_meta['date'] = float(results[0][0])
        file_meta['size'] = int(results[0][1])
        file_meta['version'] = str(results[0][2])
    return file_meta

class MySQL(object):
    """Class providing functionality for interacting with the MySQL database.

    This class serves as a wrapper for interacting with the KnowEnG MySQL

    Attributes:
        host (str): the MySQL db hostname
        user (str): the MySQL db username
        port (str): the MySQL db port
        passw (str): the MySQL db password
        database (str): the MySQL database to connect to
        conn (object): connection object for the database
        cursor (object): cursor object for the database
    """
    def __init__(self, database=None, args=None):
        """Init a MySQL object with the provided parameters.

        Constructs a MySQL object with the provided parameters, and connect to
        the relevant database.

        Args:
            database (str): the MySQL database to connect to (optional)
            args (Namespace): args as populated namespace or 'None' for defaults
        """
        if args is None:
            args = cf.config_args()
        self.user = args.mysql_user
        self.host = args.mysql_host
        self.port = args.mysql_port
        self.passw = args.mysql_pass
        self.database = database
        self.args = args
        if self.database is None:
            self.conn = sql.connect(host=self.host, port=self.port,
                                    user=self.user, password=self.passw,
                                    client_flags=[sql.ClientFlag.LOCAL_FILES])
        else:
            self.conn = sql.connect(host=self.host, port=self.port,
                                    user=self.user, password=self.passw,
                                    db=self.database,
                                    client_flags=[sql.ClientFlag.LOCAL_FILES])
        self.cursor = self.conn.cursor()

    def drop_db(self, database):
        """Remove a database from the MySQL server

        Drops the provided database from the MySQL server.

        Args:
            database (str): name of the database to remove from the MySQL server
        """
        self.cursor.execute('DROP DATABASE IF EXISTS ' + database + ';')
        self.conn.commit()

    def init_knownet(self):
        """Inits the Knowledge Network MySQL DB.

        Creates the KnowNet database and all of its tables if they do not
        already exist. Also imports the edge_type, node_type, and species
        files, but ignores any lines that have the same unique key as those
        already in the tables.
        """
        import_tables = ['node_type.txt', 'edge_type.txt']
        mysql_dir = os.sep + os.path.join(self.args.code_path, 'mysql')
        if os.path.isdir(self.args.working_dir):
            mysql_dir = self.args.working_dir + mysql_dir
        self.import_schema('KnowNet', os.path.join(mysql_dir, 'KnowNet.sql'))
        for table in import_tables:
            tablefile = os.path.join(mysql_dir, table)
            self.import_table('KnowNet', tablefile, '--ignore')
        #self.cursor.execute("SET @@GLOBAL.SQL_MODE = REPLACE(@@SQL_MODE, " + \
        #                    "'NO_ZERO_DATE', '')")
        self.conn.commit()

    def create_db(self, database):
        """Add a database to the MySQL server

        Adds the provided database from the MySQL server.

        Args:
            database (str): name of the database to add to the MySQL server
        """
        self.cursor.execute('CREATE DATABASE IF NOT EXISTS ' + database + ';')
        self.conn.commit()

    def use_db(self, database):
        """Use a database from the MySQL server

        Use the provided database from the MySQL server.

        Args:
            database (str): name of the database to use from the MySQL server
        """
        self.cursor.execute('USE ' + database + ';')
        self.conn.commit()

    def create_table(self, tablename, cmd=''):
        """Add a table to the MySQL database.

        Adds the provided tablename to the MySQL database. If cmd is specified,
        it will create the table using the provided cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): optional string to overwrite default create table
        """
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + tablename + ' ' +
                            cmd + ';')
        self.conn.commit()

    def create_temp_table(self, tablename, cmd=''):
        """Add a table to the MySQL database.

        Adds the provided tablename to the MySQL database. If cmd is specified,
        it will create the table using the provided cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): optional additional command
        """
        self.cursor.execute('CREATE TEMPORARY TABLE IF NOT EXISTS ' + \
                            tablename + ' ' + cmd + ';')
        self.conn.commit()

    def load_data(self, filename, tablename, cmd='', sep='\\t', enc='"'):
        """Import data into table in the MySQL database.

        Loads the data located on the local machine into the provided MySQL
        table. Uses the LOAD DATA LOCAL INFILE command.

        Args:
            filename (str): name of the file to import from
            tablename (str): name of the table to import into
            sep (str): separator for fields in file
            enc (str): enclosing character for fields in file
            cmd (str): optional additional command
        """
        self.cursor.execute("LOAD DATA LOCAL INFILE '" + filename +
                            "' INTO TABLE " + tablename +
                            " FIELDS TERMINATED BY '" + sep + "'" +
                            " OPTIONALLY ENCLOSED BY '" + enc + "' " +
                            cmd + ";")
        self.conn.commit()

    def drop_temp_table(self, tablename):
        """Remove a temporary table from the MySQL database

        Drops the provided tablename from the MySQL database.

        Args:
            tablename (str): name of the table to remove from the MySQL database
        """
        self.cursor.execute('DROP TEMPORARY TABLE IF EXISTS ' + tablename + ';')
        self.conn.commit()

    def drop_table(self, tablename):
        """Remove a table from the MySQL database

        Drops the provided tablename from the MySQL database.

        Args:
            tablename (str): name of the table to remove from the MySQL database
        """
        self.cursor.execute('DROP TABLE IF EXISTS ' + tablename + ';')
        self.conn.commit()

    def move_table(self, old_database, old_table, new_database, new_table):
        """Move a table in the MySQL database

        Moves the provided tablename to the MySQL database.

        Args:
            old_database (str): name of the database to move from
            old_table (str): name of the table to move from
            new_database (str): name of the database to move to
            new_table (str): name of the table to move to
        """
        self.cursor.execute('ALTER TABLE ' + old_database + '.' + old_table +
                            ' RENAME ' + new_database + '.' + new_table + ';')
        self.conn.commit()

    def copy_table(self, old_database, old_table, new_database, new_table):
        """Copy a table in the MySQL database

        Copy the provided tablename to the MySQL database.

        Args:
            old_database (str): name of the database to move from
            old_table (str): name of the table to move from
            new_database (str): name of the database to move to
            new_table (str): name of the table to move to
        """
        table1 = old_database + '.' + old_table
        table2 = new_database + '.' + new_table
        self.create_table(table2, ' LIKE ' + table1)
        cmd = 'INSERT INTO ' + table2 + ' SELECT * FROM ' + table1
        self.cursor.execute(cmd)
        self.conn.commit()

    def insert(self, tablename, cmd):
        """Insert into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): a valid SQL command to use for inserting into tablename
        """
        self.cursor.execute('INSERT INTO ' + tablename + ' ' + cmd + ';')
        self.conn.commit()

    def set_isolation(self, duration='', level='REPEATABLE READ'):
        """Sets the transaction isolation level.

        Modify the transaction isolation level to modulate lock status behavior.
        Default InnoDB is repeatable read. For other levels check online at
        https://dev.mysql.com/doc/refman/5.7/en/set-transaction.html

        Args:
            duration (str): time for isolation level to be used. Can be empty,
                GLOBAL, or SESSION
            level (str): isolation level. In order of locking level:
                SERIALIZABLE, REPEATABLE READ, READ COMMITTED, READ UNCOMMITTED
        """
        cmd = 'SET ' + duration + ' TRANSACTION ISOLATION LEVEL ' + level + ';'
        self.cursor.execute(cmd)

    def start_transaction(self, level='REPEATABLE READ'):
        """Starts a mysql transaction with the provided isolation level

        Uses the provided isolation level to start a MySQL transaction using
        the current connection. Transaction persists until the next commit.

        Args:
            level (str): isolation level. In order of locking level:
                SERIALIZABLE, REPEATABLE READ, READ COMMITTED, READ UNCOMMITTED
        """
        self.conn.start_transaction(isolation_level=level)

    def replace(self, tablename, cmd):
        """Insert into tablename using cmd.

        Replace into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): a valid SQL command to use for inserting into tablename
        """
        self.cursor.execute('REPLACE INTO ' + tablename + ' ' + cmd + ';')
        self.conn.commit()

    def replace_safe(self, tablename, cmd, values):
        """Insert into tablename using cmd.

        Replace into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): a valid SQL command to use for inserting into tablename
        """
        self.cursor.execute('REPLACE INTO ' + tablename + ' ' + cmd + ';', values)
        self.conn.commit()

    def insert_ignore(self, tablename, cmd=''):
        """Insert ignore into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): a valid SQL command to use for inserting into tablename
        """
        self.cursor.execute('INSERT IGNORE INTO ' + tablename + ' ' + cmd + ';')
        self.conn.commit()

    def run(self, cmd):
        """Run the provided command in MySQL.

        This runs the provided command using the current MySQL connection and
        cursor.

        Args:
            cmd (str): the SQL command to run on the MySQL server

        Returns:
            list: the fetched results
        """
        self.cursor.execute(cmd + ';')
        try:
            results = self.cursor.fetchall()
        except sql.Error:
            results = list()
        self.conn.commit()
        return results

    def query_distinct(self, query, table, cmd=''):
        """Run the provided query distinct in MySQL.

        This runs the provided distinct query from the provided table with the
        optional extra cmd using the current MySQL connection and cursor. It
        then returns the fetched results.

        Args:
            query (str): the SQL query to run on the MySQL server
            table (str): the table to query from
            cmd (str): the addtional SQL command to run on the MySQL server
                (optional)

        Returns:
            list: the fetched results
        """
        cmd = 'SELECT DISTINCT ' + query + ' FROM ' + table + ' ' + cmd + ';'
        self.cursor.execute(cmd)
        return self.cursor.fetchall()

    def import_schema(self, database, sqlfile):
        """Import the schema for the provided database from sqlfile.

        Removes the provided database if it exists, creates a new one, and
        imports the schema as defined in the provided sqlfile.

        Args:
            database (str): name of the database to add to the MySQL server
            sqlfile (str): name of the sql file specifying the format for the
                        database
        """
        self.create_db(database)
        cmd = ['mysql', '-u', self.user, '-h', self.host, '--port', self.port,
               '--password='+self.passw, database, '<', sqlfile]
        subprocess.check_call(' '.join(cmd), shell=True)

    def import_table(self, database, tablefile, import_flags='--delete'):
        """Import the data for the table in the provided database described by
        tablefile.

        Imports the data as defined in the provided tablefile.

        Args:
            database (str): name of the database to add to the MySQL server
            tablefile (str): name of the txt file specifying the data for the
                table
            import_flag (str): additional flags to pass to mysqlimport
        """
        cmd = ['mysqlimport', '-u', self.user, '-h', self.host, '--port',
               self.port, '--password='+self.passw, import_flags,
               database, '-L', tablefile, '-v']
        subprocess.call(' '.join(cmd), shell=True)

    def dump_table(self, table, file):
        """Dump the data for the table in the provided file(name).
        """
        cmd = ['mysql', '-u', self.user, '-h', self.host, '--port', self.port,
               '--password='+self.passw, self.database, "--execute 'SELECT * FROM", table,
               "' --batch --silent >", file]
        subprocess.check_call(' '.join(cmd), shell=True)


    def disable_keys(self):
        """Disables keys for faster operations.

        Turns off autocommit, unique_checks, and foreign_key_checks for
        the MySQLdatabase.
        """
        self.cursor.execute('SET autocommit=0;')
        self.cursor.execute('SET unique_checks=0;')
        self.cursor.execute('SET foreign_key_checks=0;')
        self.conn.commit()

    def enable_keys(self):
        """Enables keys for safer operations.

        Turns on autocommit, unique_checks, and foreign_key_checks for
        the MySQLdatabase.
        """
        self.cursor.execute('SET autocommit=1;')
        self.cursor.execute('SET unique_checks=1;')
        self.cursor.execute('SET foreign_key_checks=1;')
        self.conn.commit()

    def close(self):
        """Close connection to the MySQL server.

        This commits any changes remaining and closes the connection to the
        MySQL server.
        """
        self.conn.commit()
        self.conn.close()

def main():
    """Deploy a MySQL container using marathon with the provided command line
    arguements.

    This uses the provided command line arguments and the defaults found in
    config_utilities to launch a MySQL docker container using marathon.
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    deploy_container(args)

if __name__ == "__main__":
    main()
