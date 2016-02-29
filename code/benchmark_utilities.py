"""

Class Description:

Used to benchmark database functionalities

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
from random import randrange, sample
import math
import sys

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
                
            
    def __checkequalbins(self, bin_list, total, percentallowance):
        '''
        Private method used to determine if the bins are at least percentallowance * total
        This is a test to see if the bins are mostly reasonably sized bins
        '''
        allowance = int(percentallowance*total)
        print("The allowance is "+str(allowance))
        
        for bin_size in bin_list:
            if(bin_size < allowance):
                return False
   
        return True
    
    def multithreaded_stress_test(self, table, key, set_serialized):
        """
        Description:
        
        Benchmarks lock performance a series of multithreaded inserts into database
        Implements a huerisitic to generate equal partition bins of size 10 of the data.
        """

        heuristic_indexes = [0,1,2,3,4,5,6,7,8,9]
        selected_heuristic = -1
        
        for heuristic in heuristic_indexes:
            heuristic_query = "select CAST(substring(tmp."+key+",char_length(tmp."+key+")-"+str(heuristic)+",1) AS UNSIGNED) as bin, count(*) from (select * from "+table+") as tmp group by bin;"
            
            selected_heuristic = heuristic
            total = 0
            tmp_list = []
            
            for result in self.cursor.execute(heuristic_query,multi=True):
                res = result.fetchall()
                
                for step in res:
                    total = total + int(step[1])
                    tmp_list.append(int(step[1]))
                    
            if(self.__checkequalbins(tmp_list, total, 0.05)):
                print("The huerisitic value is "+str(selected_heuristic))
                break
    
        threads = []
        thread_data = {'num_threads':len(heuristic_indexes),'total_time':0.0,'thread_timings':[]}
        for i in heuristic_indexes:
            multithreaded_query = "select * from (select CAST(substring(tmp."+key+",char_length(tmp."+key+")-"+str(selected_heuristic)+",1) AS UNSIGNED) as bin, tmp.* from (select * from "+table+") as tmp) as data where data.bin="+str(i)+"";
            threads.append(BenchmarkWorker(self.host,self.port,self.user,self.passw,self.database, multithreaded_query))

        startt = time()
        if(not set_serialized):
            for th in threads:
                # This causes the thread to run()
                th.start() 
                
            for th in threads:
                # This waits until the thread has completed
                th.join() 
                #thread_data['total_time'] += th.execution_time
                thread_data['thread_timings'].append(th.execution_time)
            thread_data['total_time'] =  time() - startt 
            print(thread_data)
        else:
            for th in threads:
                # This causes the thread to run()
                th.start()
                th.join()
                #thread_data['total_time'] += th.execution_time
                thread_data['thread_timings'].append(th.execution_time)
            thread_data['total_time'] =  time() - startt
            print(thread_data)
            

        
    def overlapping_multithreaded_select_test(self, table, key, percentoverlap):
        """
        Used to benchmark database functions when there are overlapping selects being
        done by multiple connections. Identifies lock bottlenecks.
        """
        heuristic_indexes = [0,1,2,3,4,5,6,7,8,9]
        selected_heuristic = -1
        
        for heuristic in heuristic_indexes:
            heuristic_query = "select CAST(substring(tmp."+key+",char_length(tmp."+key+")-"+str(heuristic)+",1) AS UNSIGNED) as bin, count(*) from (select * from "+table+") as tmp group by bin;"
            
            selected_heuristic = heuristic
            total = 0
            tmp_list = []
            
            for result in self.cursor.execute(heuristic_query,multi=True):
                res = result.fetchall()
                
                for step in res:
                    total = total + int(step[1])
                    tmp_list.append(int(step[1]))
                    
            if(self.__checkequalbins(tmp_list, total, 0.05)):
                print("The huerisitic value is "+str(selected_heuristic))
                break
    
        threads = []
        thread_data = {'num_threads':len(heuristic_indexes),'total_time':0.0,'thread_timings':[]}
        for i in heuristic_indexes:
            new_list = [x for x in heuristic_indexes if x!=i]
            bins = sample(set(heuristic_indexes),int(percentoverlap*10))
            multithreaded_query = "select * from (select CAST(substring(tmp."+key+",char_length(tmp."+key+")-"+str(selected_heuristic)+",1) AS UNSIGNED) as bin, tmp.* from (select * from "+table+") as tmp) as data where data.bin="+str(i)+""
            for bin in bins:
                multithreaded_query += " OR data.bin="+str(bin)+""
            
            threads.append(BenchmarkWorker(self.host,self.port,self.user,self.passw,self.database, multithreaded_query))

        for th in threads:
            # This causes the thread to run()
            th.start() 
            
        for th in threads:
            # This waits until the thread has completed
            th.join() 
            thread_data['total_time'] += th.execution_time
            thread_data['thread_timings'].append(th.execution_time)
        print(thread_data)
        
    
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
    def __init__(self, host, port, user, password, database, query):
        #super(BenchmarkWorker, self).__init__()
        #self._stop = threading.Event()
        threading.Thread.__init__(self)
        self.threadLock = threading.Lock()
        self.query = query
        self.database = database
        self.conn = sql.connect(host=host, port=port,
                                user=user, password=password,
                                db=database,
                                client_flags=[sql.ClientFlag.LOCAL_FILES])
        self.execution_time = None
        
    #def stopit(self):
    #    print("Stoppping...")
    #    self._stop.set()
        
    #def stopped(self):
    #    return self._stop.is_set()
            
    def run(self):
        print("Starting with query: "+self.query)
        #while not self.stopped():                
        cur = self.conn.cursor()
        start = time()
        try:
            cur.execute(self.query)
            res = cur.fetchall()
            #self.conn.commit()
        except Exception as e:
            print("Thread terminating with "+str(e))
            sys.exit(0)
        end = time()
        cur.close()
        self.conn.close()
        self.threadLock.acquire()
        print("The total time taken to run query: "+self.query+" is "+str(end-start))
        self.execution_time = end-start
        #logging.info('Selecting %s rows from indexes between [%s, %s] took %.2f seconds...' % (settings.SELECT_ROW_COUNT, self.id_min, self.id_max, (end - start),))
        self.threadLock.release()
