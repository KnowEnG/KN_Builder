"""Place to store global variables

Classes:

Functions:

Variables:
    DEFAULT_DOCKER_IMG: docker image to run pipeline steps
    DEFAULT_CURL_URL: address of chronos scheduler
    DEFAULT_LOCAL_BASE: toplevel directory on local machine
    DEFAULT_CLOUD_BASE: toplevel directory on shared cloud storage

    DEFAULT_CODE_PATH: relative path of code dir from toplevel
    DEFAULT_DATA_PATH: relative path of data dir from toplevel
    DEFAULT_MAP_PATH: relative path of id_map dir from toplevel

    DEFAULT_MYSQL_URL = location of MySQL db
    DEFAULT_MYSQL_PORT = port for MySQL db
    DEFAULT_MYSQL_USER = user for MySQL db
    DEFAULT_MYSQL_PASS = password for MySQL db

"""

import os

DEFAULT_DOCKER_IMG = 'cblatti3/py3_mysql:0.1'
DEFAULT_CURL_URL = 'mmaster02.cse.illinois.edu:4400'
DEFAULT_LOCAL_BASE = '/workspace/apps/P1_source_check'
DEFAULT_CLOUD_BASE = '/mnt/storage/post3/apps/P1_source_check/'

DEFAULT_CODE_PATH = 'code'
DEFAULT_DATA_PATH = 'raw_downloads'
DEFAULT_MAP_PATH = 'id_map'

DEFAULT_MYSQL_URL = 'knowice.cs.illinois.edu'
DEFAULT_MYSQL_PORT = '3308'
DEFAULT_MYSQL_USER = 'root'
DEFAULT_MYSQL_PASS = 'KnowEnG'

DEFAULT_REDIS_URL = os.environ["REDIS_PORT_6379_TCP_ADDR"]
DEFAULT_REDIS_PORT = os.environ["REDIS_PORT_6379_TCP_PORT"]