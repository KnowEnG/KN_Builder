"""Utiliites for interacting with the KnowEnG MySQL db through python.

Classes:
    MySQL: Extends the object class to provide functions neeeded format
        interacting with the MySQL DB.

Functions:

Variables:
"""

import config_utilities as cf
import mysql.connector as sql
import subprocess

def get_database():
    """Returns an object of the MySQL class.

    This returns an object of the MySQL class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return MySQL()

def import_ensembl(alias):
    """Imports the ensembl data for the provided alias into the KnowEnG
    database.

    This produces the local copy of the fetched ensembl database for alias.
    It drops the existing database, creates a new database, imports the
    relevant ensembl sql schema, and imports the table.

    Args:
        alias (str): An alias defined in ensembl.aliases.
    
    Returns:
    """
    db = MySQL()
    db.import_schema(alias, 'schema.sql')
    db.import_table(alias, '*.txt')


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

def combine_tables(alias):
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
    db = MySQL(alias_db)
    db.create_table(tablename, get_insert_cmd('gene'))
    for step in steps:
        db.insert(tablename, get_insert_cmd(step))
    db.drop_table(combined_db + '.' + combined_table)
    db.move_table(alias_db, tablename, combined_db, combined_table)
    db.use_db(combined_db)
    cmd = ("SELECT *, db_display_name AS species FROM " + alias + "_mappings "
            "WHERE 1=2")
    db.create_table(all_table, cmd)
    cmd = ("DELETE FROM all_mappings WHERE species = '" + alias + "'")
    db.execute(cmd)
    cmd = ("SELECT *, '" + alias + "' AS species FROM " + alias + "_mappings")
    db.insert(all_table, cmd)
    db.close()

class MySQL(object):
    """Class providing functionality for interacting with the MySQL database.

    This class serves as a wrapper for interacting with the KnowEnG MySQL db.MySQL

    Attributes:
        host (str): the MySQL db hostname
        user (str): the MySQL db username
        port (str): the MySQL db port
        passw (str): the MySQL db password
        database (str): the MySQL database to connect to
        conn (object): connection object for the database
        cursor (object): cursor object for the database
    """
    def __init__(self, database = None):
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
        if self.database is None:
            self.conn = sql.connect( host=self.host, port=self.port,
                                    user=self.user, password=self.passw)
        else:
            self.conn = sql.connect( host=self.host, port=self.port,
                                    user=self.user, password=self.passw,
                                    db = self.database)
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

    def create_table(self, tablename, cmd = ''):
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
        """
        self.cursor.execute(cmd + ';')
        self.conn.commit()

    def import_schema(self, database, sqlfile):
        """Import the schema for the provided database from sqlfile.

        Removes the provided database if it exists, creates a new one, and imports
        the schema as defined in the provided sqlfile.

        Args:
            database (str): name of the database to add to the MySQL server
            sqlfile (str): name of the sql file specifying the format for the
                        database

        Returns:
        """
        self.drop_db(database)
        self.create_db(database)
        cmd = ['mysql', '-u', self.user, '-h', self.host, '--port', self.port,
                '--password='+self.passw, database, '<', sqlfile]
        subprocess.call(' '.join(cmd), shell=True)

    def import_table(self, database, tablefile):
        """Import the data for the table in the provided database described by
        tablefile.

        Imports the data as defined in the provided tablefile.

        Args:
            database (str): name of the database to add to the MySQL server
            tablefile (str): name of the txt file specifying the data for the
                        table

        Returns:
        """
        cmd = ['mysqlimport', '-u', self.user, '-h', self.host, '--port',
                self.port, '--password='+self.passw, '--delete',
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
