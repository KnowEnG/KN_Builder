import unittest
from benchmark_utilities import MySQLBenchmark

class MySQLBenchmarkUtilsTestBench(unittest.TestCase):
    """Tests for benchmark_utilities functionality by building benchmark data and making a submission to an elasticsearch instance."""

    def __init__(self, *args, **kwargs):
        super(MySQLBenchmarkUtilsTestBench, self).__init__(*args, **kwargs)
        self.benchmark_object = MySQLBenchmark()

    def test_db_configured_for_profiling(self):
        self.assertEqual(self.benchmark_object.check_db_set_for_profiling(), True)            
            
    def test_generate_table_details(self):
        '''
        Description:

        Used to validate that the Benchmark Utilities produce the
        right table description object for a given table (raw_line)
        '''
        expected = [{'Default': None,
          'Extra': '',
          'Field': 'file_id',
          'Key': 'PRI',
          'Null': 'NO',
          'Type': 'varchar(40)'},
         {'Default': None,
          'Extra': '',
          'Field': 'line_num',
          'Key': 'PRI',
          'Null': 'NO',
          'Type': 'int(11)'},
         {'Default': None,
          'Extra': '',
          'Field': 'line_hash',
          'Key': 'PRI',
          'Null': 'NO',
          'Type': 'varchar(40)'},
         {'Default': None,
          'Extra': '',
          'Field': 'line_str',
          'Key': '',
          'Null': 'NO',
          'Type': 'text'}]
        
        data = self.benchmark_object.gettabledetails('raw_line')
        
        for col in data:
            field = col['Field']
            found = False
            for e_col in expected:
                if(field == e_col['Field']):
                    found = 1
                    self.assertEqual(col['Default'], e_col['Default'])
                    self.assertEqual(col['Extra'], e_col['Extra'])
                    self.assertEqual(col['Field'], e_col['Field'])
                    self.assertEqual(col['Key'], e_col['Key'])
                    self.assertEqual(col['Null'], e_col['Null'])
                    self.assertEqual(col['Type'], e_col['Type'])
                    break

            self.assertTrue(found)
                
     
    def test_send_data_to_ES(self):
        data = self.benchmark_object.schema_storage_info("ALL")
        self.benchmark_object.send_data_to_ES(data)
    #def test_query_DNE(self):
    #    pass

if __name__ == '__main__':
    unittest.main()
