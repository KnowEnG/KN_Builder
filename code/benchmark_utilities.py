"""

Class Description:

Used to benchmark database function

"""

import config_utilities as cf
import mysql.connector as sql
import os
import json
import subprocess
from time import time
import threading
import logging
from time import time, sleep
from random import randrange


class MySQLBenchmark:
    
    """
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
        """Init a MySQLBenchmark Object
        
        Args:
        database (str): the MySQL database to connect to (optional)
        """
        self.user = cf.DEFAULT_MYSQL_USER
        self.host = cf.DEFAULT_MYSQL_URL
        #print(self.host)
        self.port = cf.DEFAULT_MYSQL_PORT
        self.passw = cf.DEFAULT_MYSQL_PASS
        #print(self.passw)
        self.database = "KnowNet"
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
        

    """
    Description: The database has to be configured to be able to generate the
    statistics for queries that we use. This is as per the following document: 
    http://www.pythian.com/blog/mysql-query-profiling-with-performance-schema/
    
    ** This is a one-time setup of the database so we must first verify that this 
    step has not already been configured. **
    """
    def check_db_set_for_profiling(self):
        
        check_query = "SELECT * FROM performance_schema.setup_consumers where name = 'events_statements_history_long';"
        self.cursor.execute(config_query1)
        
    
    def config_db_for_profiling(self):
     
        #This enables the stage* performance tables"
        config_query1 = "update performance_schema.setup_instruments set enabled='YES', timed='YES';"    
        #This enables the events_statements_history* and events_stages_history* performance  tables
        config_query2 = "update performance_schema.setup_consumers set enabled='YES';"
        
        #Need to check if permissions are allowed for the user to make this adjustment
        self.cursor.execute(config_query1)
        self.cursor.execute(config_query2)
        print("The database has been configured for performance statisics and analysis.")

    def connection_stress_test(self, stress_level):            
        start = time()
        for i in range(stress_level):
            conn = sql.connect(host=self.host, port=self.port, user=self.user, password=self.passw, client_flags=[sql.ClientFlag.LOCAL_FILES])
            conn.close();

        end = time()
        print("Time taken to execute connections: %d is %f", stress_level, (end-start))
        
    def multithreaded_stress_test(self):
        """
        Description:
        
        Benchmarks lock performance a series of multithreaded inserts into database
        """
        pass
        
    def overlapping_multithreaded_select_test(self):
        """
        Used to benchmark database functions when there are overlapping selects being
        done by multiple connections. Identifies lock bottlenecks.
        """
        pass

    def query_execution_time(self, query):
        start = time()
        self.cursor.execute(query)
        end = time()
        print("Time taken to execute QUERY:"+query+", is "+str(end-start))
        
    def get_query_id(self, query):
        get_id_query = "SELECT EVENT_ID, TRUNCATE(TIMER_WAIT/1000000000000,6) as Duration, SQL_TEXT FROM performance_schema.events_statements_history_long WHERE SQL_TEXT like '%"+str(query)+"%';"
        print(get_id_query)
        for result in self.cursor.execute(get_id_query,multi=True):
            data = result.fetchall()
            print(data)
            return data[0][0]
        
    """
    Obtains the breakdown of generating the MySQL query in terms of seconds
    """
    def query_time_breakdown(self,query):
        self.cursor.execute(query)
        id = self.get_query_id(query)
        print(id)
        query_breakdown_query ="SELECT event_name AS Stage, TRUNCATE(TIMER_WAIT/1000000000000,6) AS Duration FROM performance_schema.events_stages_history_long WHERE NESTING_EVENT_ID="+id+";"
        for result in self.cursor.execute(query_breakdown_query,multi=True):
            print(result.fetchall())
            
    
    def query_execution_plan(self, query):
        explain_query = "EXPLAIN EXTENDED  "+str(query)+""
        execution_plan = []
        for result in self.cursor.execute(explain_query,multi=True):
            res = result.fetchall()
            for step in res:
                data = {}
                data['id'] = step[0]
                data['select_type'] = step[1]
                data['table'] = step[2]
                data['type'] = step[3]
                data['possible_keys'] = step[4]
                data['key'] = step[5]
                data['key_len'] = step[6]
                data['ref'] = step[7]
                data['rows'] = step[8]
                data['filtered'] = step[9]
                data['Extra'] = step[10]
                execution_plan.insert(0,data)
        print(execution_plan)
        return execution_plan

    def gettabledetails(self, tablename):
        desc_query = "DESCRIBE "+str(tablename)
        table_desc = []
        for result in self.cursor.execute(desc_query,multi=True):
            res = result.fetchall()
            for field in res:
                data = {}
                data['Field'] = field[0]
                data['Type'] = field[1]
                data['Null'] = field[2]
                data['Key'] = field[3]
                data['Default'] = field[4]
                data['Extra'] = field[5]
                table_desc.append(data)
        print(table_desc)
        return table_desc

    class BenchmarkWorker(threading.Thread):
        def __init__(self, id_min, id_max, database,conn):
            super(Worker, self).__init__()
            self._stop = threading.Event()
            self.id_min = id_min
            self.id_max = id_max
            self.database = database
            self.conn = conn

            def stop(self):
                #logging.debug('Stopping...')
                self._stop.set()

            def stopped(self):
                return self._stop.isSet()

            def run(self):
                #logging.debug('Starting...')
                while not self.stopped():
                    start = time()
                    conn = self.conn
                    cur = conn.cursor()
                    for i in xrange(settings.SELECT_ROW_COUNT):
                        cur.execute('SELECT * FROM ' + self.database + ' WHERE id = %s', (randrange(self.id_min, self.id_max),))
                    conn.commit()
                    cur.close()
                    conn.close()
                    end = time()
                    #logging.info('Selecting %s rows from indexes between [%s, %s] took %.2f seconds...' % (settings.SELECT_ROW_COUNT, self.id_min, self.id_max, (end - start),))



