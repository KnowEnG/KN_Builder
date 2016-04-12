"""Utiliites for interacting with the KnowEnG Databases through python.

Contains the class Database which provides functionality for interacting with
various databases 

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

import config_utilities as cf
import os
import json
import subprocess

class Database(object):
    """Class providing functionality for interacting with the various databases.

    This class serves as a wrapper for interacting with the KnowEnG Databases

    Attributes:
        host (str): the db hostname
        user (str): the db username
        port (str): the db port
        passw (str): the db password
        database (str): the database to connect to
        conn (object): connection object for the database
        cursor (object): cursor object for the database
    """
    def __init__(self, database=None, args=None):
        """Init a Database object with the provided parameters.

        Constructs a Database object with the provided parameters, and connect to
        the relevant database.

        Args:
            database (str): the database to connect to (optional)
            args (Namespace): args as populated namespace or 'None' for defaults
        """
        if args is None:
            args=cf.config_args()
        self.user = args.db_user
        self.host = args.db_host
        self.port = args.db_port
        self.passw = args.db_pass
        self.database = database
        self.args = args
        self.debug_mode = False
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
        """Remove a database from the database instance

        Drops the provided database.

        Args:
            database (str): name of the database to remove
        """
        raise NotImplementedError("Please Implement 'drop_db' method")
        
            
    def init_knownet(self):
        """Inits the Knowledge Network for given Database instance

        Creates the KnowNet database and all of its tables if they do not
        already exist. Also imports the edge_type, node_type, and species
        files, but ignores any lines that have the same unique key as those
        already in the tables.
        """
        raise NotImplementedError("Please Implement 'init_knownet' method")


    def create_db(self, database):
        """
        Adds the provided database from database server.

        Args:
            database (str): name of the database to add to the MySQL server
        """
        raise NotImplementedError("Please Implement 'create_db' method")

    def use_db(self, database):
        """
        Use the provided database from the Database server.

        Args:
            database (str): name of the database to use from the database server
        """
        raise NotImplementedError("Please Implement 'use_db' method")

    def create_table(self, tablename, cmd=''):
        """Add a table to the database.

        Adds the provided tablename to the database. If cmd is specified,
        it will create the table using the provided cmd.

        Args:
            tablename (str): name of the table to add to the database
            cmd (str): optional string to overwrite default create table
        """
        raise NotImplementedError("Please Implement 'create_table' method")


    def create_temp_table(self, tablename, cmd=''):
        """Add a table to the database.

        Adds the provided tablename to the database. If cmd is specified,
        it will create the table using the provided cmd.

        Args:
            tablename (str): name of the table to add to the database
            cmd (str): optional additional command
        """
        raise NotImplementedError("Please Implement 'create_temp_table' method")

    def load_data(self, filename, tablename, cmd='', sep='\\t', enc='"'):
        """Import data into table in the database.

        Loads the data located on the local machine into the provided database
        table.

        Args:
            filename (str): name of the file to import from
            tablename (str): name of the table to import into
            sep (str): separator for fields in file
            enc (str): enclosing character for fields in file
            cmd (str): optional additional command
        """
        raise NotImplementedError("Please Implement 'load_data' method")

    def drop_temp_table(self, tablename):
        """Remove a temporary table from the database

        Drops the provided tablename from the database.

        Args:
            tablename (str): name of the table to remove from the database
        """
        raise NotImplementedError("Please Implement 'drop_temp_table' method")

    def drop_table(self, tablename):
        """Remove a table from the database

        Drops the provided tablename from the database.

        Args:
            tablename (str): name of the table to remove from the database
        """
        raise NotImplementedError("Please Implement 'drop_table' method")

    def move_table(self, old_database, old_table, new_database, new_table):
        """Move a table in the database

        Moves the provided tablename to the database.

        Args:
            old_database (str): name of the database to move from
            old_table (str): name of the table to move from
            new_database (str): name of the database to move to
            new_table (str): name of the table to move to
        """
        raise NotImplementedError("Please Implement 'move_table' method")


    def copy_table(self, old_database, old_table, new_database, new_table):
        """Copy a table in the database

        Copy the provided tablename to the database.

        Args:
            old_database (str): name of the database to move from
            old_table (str): name of the table to move from
            new_database (str): name of the database to move to
            new_table (str): name of the table to move to
        """
        raise NotImplementedError("Please Implement 'copy_table' method")


    def insert(self, tablename, cmd):
        """Insert into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the database
            cmd (str): a valid SQL command to use for inserting into tablename
        """
        raise NotImplementedError("Please Implement 'insert' method")

    def replace(self, tablename, cmd):
        """Insert into tablename using cmd.

        Replace into tablename using cmd.

        Args:
            tablename (str): name of the table to add to the database
            cmd (str): a valid command to use for inserting into tablename
        """
        raise NotImplementedError("Please Implement 'replace' method")



    def run(self, cmd):
        """Run the provided command in database.

        This runs the provided command using the current connection and cursor.

        Args:
            cmd (str): the SQL command to run on the server

        Returns:
            list: the fetched results
        """
        raise NotImplementedError("Please Implement 'run' method")


    def import_schema(self, database, sqlfile):
        """Import the schema for the provided database from sqlfile.

        Removes the provided database if it exists, creates a new one, and
        imports the schema as defined in the provided sqlfile.

        Args:
            database (str): name of the database to add to the database server
            sqlfile (str): name of the sql file specifying the format for the
                        database
        """
        raise NotImplementedError("Please Implement 'import_schema' method")


    def import_table(self, database, tablefile, import_flags='--delete'):
        """Import the data for the table in the provided database described by
        tablefile.

        Imports the data as defined in the provided tablefile.

        Args:
            database (str): name of the database to add to the database server
            tablefile (str): name of the txt file specifying the data for the
                table
            import_flag (str): additional flags to pass
        """
        raise NotImplementedError("Please Implement 'import_table' method")


    def close(self):
        """Close connection to the database server.

        This commits any changes remaining and closes the connection to the
        server.
        """
        raise NotImplementedError("Please Implement 'close' method")
    
    def set_debug_mode(self, trueorfalse):
        self.debug_mode = trueorfalse
        
    def get_debug_mode(self):
        return self.debug_mode

    def generate_perf_data(self, root_method_name):
        """
        Generate dictionary (json) template for performance benchmarking data
        """
        perf_data = {
            "root_method": root_method_name,
            "components" : []
        }
        return perf_data


    def add_perf_component_json(self, perf_data, component_name, component_data):
        """
        Add performance component to performance data dictionary, with order_id, component_name and component performance data
        """
        component_size = len(perf_data["components"])
        component = {"order_id" : component_size + 1, "component_name": component_name, "component_data" : component_data}
        perf_data["components"].append(component)

        return perf_data
    
    def flush_perf_json(self):
        print(self.json_base)
