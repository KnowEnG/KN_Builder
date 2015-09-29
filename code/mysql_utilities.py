"""Utiliites for interacting with the KnowEnG MySQL db through python.

Classes:
    MySQL: Extends the object class to provide functions neeeded format
        interacting with the MySQL DB.

Functions:
    combine_tables(str): Combine all of the data imported for the provided
        alias (str) into a single db
    create_dictionary(list)->dict: Creates a dictionary from a MySQL fetched
        results
    create_mapping_dicts(str): Creates the mapping dictionaries for the
        provided alias (str)
    get_database: Returns an object of the MySQL class
    get_insert_cmd(str)->str: Returns the MySQL command to be used with an
        insert for the provided step
    import_ensembl(str): Imports the ensembl data for the provided alias (str)
        into the KnowEnG database

Variables:
"""

import config_utilities as cf
import mysql.connector as sql
import os
import json
import subprocess

def combine_tables(alias, args=cf.config_args()):
    """Combine all of the data imported from ensembl for the provided alias
    into a single database.

    This combines the imported tables into a single table knownet_mappings with
    information from genes, transcripts, and translations. It then merges this
    table into the KnowNet database for use in gene identifier mapping.

    Args:
        alias (str): An alias defined in ensembl.aliases.

    Returns:
    """
    alias_db = 'ensembl_' + alias
    tablename = 'knownet_mappings'
    combined_db = 'KnowNet'
    combined_table = alias + '_mappings'
    all_table = 'all_mappings'
    steps = ['transcript', 'translation', 'transcript2stable',
             'translation2stable']
    db = MySQL(alias_db, args)
    db.create_table(tablename, get_insert_cmd('gene'))
    for step in steps:
        db.insert(tablename, get_insert_cmd(step))
    db.drop_table(combined_db + '.' + combined_table)
    db.move_table(alias_db, tablename, combined_db, combined_table)
    db.use_db(combined_db)
    cmd = ("SELECT *, db_display_name AS species FROM " + alias + "_mappings "
           "WHERE 1=2")
    db.create_table(all_table, cmd)
    #cmd = ("DELETE FROM " + all_table + " WHERE species = '" + alias + "'")
    #db.execute(cmd)
    cmd = ("SELECT *, '" + alias + "' AS species FROM " + alias + "_mappings")
    db.insert(all_table, cmd)
    db.close()

def create_dictionary(results):
    """Creates a dictionary from a MySQL fetched results.

    This returns a dictionary from the MySQL results after a query from the DB.
    It assumes there are two columns in the results and reads through all of
    the results, making them into a dictionary.

    Args:
        results: a list of the results returned from a MySQL query
    Returns:
    """
    map_dict = dict()
    for (raw, mapped) in results:
        map_dict[str(raw)] = str(mapped)
    return map_dict

def query_all_mappings(version_dict, args=cf.config_args()):
    """Creates the all mappings dictionary for the provided alias.

    Produces a dictionary of ensembl stable mappings and the all unique mappings
    the provided alias. It then saves them as json objects to
    file.

    Args:
        version_dict (dict): the version dictionary describing the
            source:alias

    Returns:
    """
    alias = version_dict['alias']
    taxid = version_dict['alias_info']
    database = 'KnowNet'
    table = alias + '_mappings'
    map_dir = os.path.join(args.data_path, cf.DEFAULT_MAP_PATH)
    if os.path.isdir(args.local_dir):
        map_dir =  os.path.join(args.local_dir, map_dir)
    if not os.path.isdir(map_dir):
        os.mkdir(map_dir)
    print(map_dir)
    db = MySQL(database, args)
    results = db.query_distinct('stable_id, stable_id', table)
    map_dict = dict()
    for (raw, mapped) in results:
        map_dict[taxid + '::ENSEMBL_STABLE_ID::' + str(raw)] = str(mapped)
    results = db.query_distinct('dbprimary_acc, db_name, stable_id', table)
    for (raw, hint, mapped) in results:
        map_dict['::'.join([taxid, str(hint), str(raw)])] = str(mapped)
    with open(os.path.join(map_dir, alias + '_all.json'), 'w') as outfile:
        json.dump(map_dict, outfile, indent=4)

def create_mapping_dicts(version_dict, args=cf.config_args()):
    """Creates the mapping dictionaries for the provided alias.

    Produces the ensembl stable mappings dictionary and the all unique mappings
    dictionary for the provided alias. It then saves them as json objects to
    file.

    Args:
        version_dict (dict): the version dictionary describing the
            source:alias

    Returns:
    """
    alias = version_dict['alias']
    taxid = version_dict['alias_info']
    database = 'KnowNet'
    table = 'all_mappings'
    cmd = "WHERE species='" + alias + "'"
    map_dir = os.path.join(args.data_path, cf.DEFAULT_MAP_PATH)
    if os.path.isdir(args.local_dir):
        map_dir =  os.path.join(args.local_dir, map_dir)
    if not os.path.isdir(map_dir):
        os.mkdir(map_dir)
    db = MySQL(database, args)
    results = db.query_distinct('stable_id, stable_id', table, cmd)
    with open(os.path.join(map_dir, alias + '_stable.json'), 'w') as outfile:
        map_dict = create_dictionary(results)
        json.dump(map_dict, outfile, indent=4)
    results = db.query_distinct('dbprimary_acc, stable_id', table, cmd)
    with open(os.path.join(map_dir, alias + '_unique.json'), 'w') as outfile:
        map_dict = create_dictionary(results)
        json.dump(map_dict, outfile, indent=4)

def get_database(args=cf.config_args()):
    """Returns an object of the MySQL class.

    This returns an object of the MySQL class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return MySQL(None, args)

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
        (str): the command to be used with an INSERT INTO statement at this
            step
    """
    if step == 'gene':
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, external_db.db_name, "
               "external_db.priority, external_db.db_display_name, "
               "gene.stable_id "
               "FROM xref INNER JOIN external_db "
               "ON xref.external_db_id = external_db.external_db_id "
               "INNER JOIN object_xref "
               "ON xref.xref_id = object_xref.xref_id "
               "INNER JOIN gene "
               "ON object_xref.ensembl_id = gene.gene_id "
               "WHERE object_xref.ensembl_object_type = 'Gene'")
    elif step == 'transcript':
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, external_db.db_name, "
               "external_db.priority, external_db.db_display_name, "
               "gene.stable_id "
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
        cmd = ("SELECT DISTINCT xref.dbprimary_acc, external_db.db_name, "
               "external_db.priority, external_db.db_display_name, "
               "gene.stable_id "
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
               "'ensembl' AS db_name, "
               "1000 AS priority, "
               "'ensembl' AS db_display_name, "
               "gene.stable_id "
               "FROM transcript "
               "INNER JOIN gene "
               "ON transcript.gene_id = gene.gene_id")
    elif step == 'translation2stable':
        cmd = ("SELECT DISTINCT translation.stable_id AS dbprimary_acc, "
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

def import_ensembl(alias, args=cf.config_args()):
    """Imports the ensembl data for the provided alias into the KnowEnG
    database.

    This produces the local copy of the fetched ensembl database for alias.
    It drops the existing database, creates a new database, imports the
    relevant ensembl sql schema, and imports the table.

    Args:
        alias (str): An alias defined in ensembl.aliases.

    Returns:
    """
    database = 'ensembl_' + alias
    db = MySQL(None, args)
    db.init_knownet()
    db.drop_db(database)
    db.import_schema(database, 'schema.sql')
    db.import_table(database, '*.txt')
    db.close()

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
    def __init__(self, database=None, args=cf.config_args()):
        """Init a MySQL object with the provided parameters.

        Constructs a MySQL object with the provided parameters, and connect to
        the relevant database.

        Args:
        database (str): the MySQL database to connect to (optional)
        """
        self.user = cf.DEFAULT_MYSQL_USER
        self.host = cf.DEFAULT_MYSQL_URL
        self.port = cf.DEFAULT_MYSQL_PORT
        self.passw = cf.DEFAULT_MYSQL_PASS
        self.database = database
        self.args = args
        if self.database is None:
            self.conn = sql.connect(host=self.host, port=self.port,
                                    user=self.user, password=self.passw)
        else:
            self.conn = sql.connect(host=self.host, port=self.port,
                                    user=self.user, password=self.passw,
                                    db=self.database)
        self.cursor = self.conn.cursor()

    def drop_db(self, database):
        """Remove a database from the MySQL server

        Drops the provided database from the MySQL server.

        Args:
            database (str): name of the database to remove from the MySQL server

        Returns:
        """
        self.cursor.execute('DROP DATABASE IF EXISTS ' + database + ';')
        self.conn.commit()

    def init_knownet(self):
        """Inits the Knowledge Network MySQL DB.

        Creates the KnowNet database and all of its tables if they do not
        already exist. Also imports the edge_type, node_type, and species
        files, but ignores any lines that have the same unique key as those
        already in the tables.

        Args:
        Returns:
        """
        import_tables = ['node_type.txt', 'edge_type.txt', 'species.txt']
        mysql_dir = os.sep + os.path.join(self.args.code_path, 'mysql')
        if os.path.isdir(self.args.local_dir):
            mysql_dir = self.args.local_dir + mysql_dir
        self.import_schema('KnowNet', os.path.join(mysql_dir, 'KnowNet.sql'))
        for table in import_tables:
            tablefile = os.path.join(mysql_dir, table)
            self.import_table('KnowNet', tablefile, '--ignore')

    def create_db(self, database):
        """Add a database to the MySQL server

        Adds the provided database from the MySQL server.

        Args:
            database (str): name of the database to add to the MySQL server

        Returns:
        """
        self.cursor.execute('CREATE DATABASE IF NOT EXISTS ' + database + ';')
        self.conn.commit()

    def use_db(self, database):
        """Use a database from the MySQL server

        Use the provided database from the MySQL server.

        Args:
            database (str): name of the database to use from the MySQL server

        Returns:
        """
        self.cursor.execute('USE ' + database + ';')
        self.conn.commit()

    def create_table(self, tablename, cmd=''):
        """Add a table to the MySQL database.

        Adds the provided tablename to the MySQL database. If cmd is specified,
        it will create the table using the provided cmd.
        Args:
            tablename (str): name of the table to add to the MySQL database

        Returns:
        """
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + tablename + ' ' +
                            cmd + ';')
        self.conn.commit()

    def drop_table(self, tablename):
        """Remove a table from the MySQL database

        Drops the provided tablename from the MySQL database.

        Args:
            tablename (str): name of the table to remove from the MySQL database

        Returns:
        """
        self.cursor.execute('DROP TABLE IF EXISTS ' + tablename + ';')
        self.conn.commit()

    def move_table(self, old_database, old_table, new_database, new_table):
        """Move a table in the MySQL database

        Moves the provided tablename to the MySQL database.

        Args:
            tablename (str): name of the table to add to the MySQL database

        Returns:
        """
        self.cursor.execute('ALTER TABLE ' + old_database + '.' + old_table +
                            ' RENAME ' + new_database + '.' + new_table + ';')
        self.conn.commit()

    def copy_table(self, old_database, old_table, new_database, new_table):
        """Copy a table in the MySQL database

        Copy the provided tablename to the MySQL database.

        Args:
            tablename (str): name of the table to add to the MySQL database

        Returns:
        """
        table1 = old_database + '.' + old_table
        table2 = new_database + '.' + new_table
        self.create_table(table2, ' LIKE ' + table1)
        cmd = 'INSERT INTO ' + table2 + ' SELECT * FROM ' + table1
        self.cursor.execute(cmd)
        self.conn.commit()

    def insert(self, tablename, cmd):
        """Insert into tablename using cmd.

        Insert into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the MySQL database
            cmd (str): a valid SQL command to use for inserting into tablename

        Returns:
        """
        self.cursor.execute('INSERT INTO ' + tablename + ' ' + cmd + ';')
        self.conn.commit()

    def execute(self, cmd):
        """Run the provided command in MySQL.

        This runs the provided command using the current MySQL connection and
        cursor.

        Args:
            cmd (str): the SQL command to run on the MySQL server

        Returns:
            (list): the fetched results
        """
        self.cursor.execute(cmd + ';')
        self.conn.commit()

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
            (list): the fetched results
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

        Returns:
        """
        self.create_db(database)
        cmd = ['mysql', '-u', self.user, '-h', self.host, '--port', self.port,
               '--password='+self.passw, database, '<', sqlfile]
        subprocess.call(' '.join(cmd), shell=True)

    def import_table(self, database, tablefile, import_flags='--delete'):
        """Import the data for the table in the provided database described by
        tablefile.

        Imports the data as defined in the provided tablefile.

        Args:
            database (str): name of the database to add to the MySQL server
            tablefile (str): name of the txt file specifying the data for the
                        table
            import_flag (str): additional flags to pass to mysqlimport

        Returns:
        """
        cmd = ['mysqlimport', '-u', self.user, '-h', self.host, '--port',
               self.port, '--password='+self.passw, import_flags,
               '--fields_escaped_by=\\\\', database, '-L', tablefile]
        subprocess.call(' '.join(cmd), shell=True)

    def close(self):
        """Close connection to the MySQL server.

        This commits any changes remaining and closes the connection to the
        MySQL server.

        Args:

        Returns:
        """
        self.conn.commit()
        self.conn.close()
