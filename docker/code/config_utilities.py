"""config module to manage global variables

This module establishes default values and argument parsers for commonly
used variables

Attributes:
    DEFAULT_CHRONOS_URL (str): address of chronos scheduler
    DEFAULT_MARATHON_URL (str): address of marathon scheduler
    DEFAULT_WORK_BASE (str): toplevel directory of working directory

    DEFAULT_CODE_PATH (str): relative path of code dir from toplevel
    DEFAULT_DATA_PATH (str): relative path of data dir from toplevel
    DEFAULT_LOGS_PATH (str): relative path of logs dir from toplevel
    DEFAULT_LOGS_PATH (str): relative path of srcClass dir from toplevel
    DEFAULT_MAP_PATH (str): relative path of id_map dir from toplevel

    DEFAULT_MYSQL_URL (str): location of MySQL db
    DEFAULT_MYSQL_PORT (int): port for MySQL db
    DEFAULT_MYSQL_USER (str): user for MySQL db
    DEFAULT_MYSQL_PASS (str): password for MySQL db
    DEFAULT_MYSQL_MEM (str): memory for launching MySQL db
    DEFAULT_MYSQL_CPU (str): CPUs for launching MySQL db
    DEFAULT_MYSQL_DIR (str): toplevel directory for MySQL db storage
    DEFAULT_MYSQL_CONF (str): name of config path for launching MySQL

    DEFAULT_REDIS_URL (str): location of Redis db
    DEFAULT_REDIS_PORT (int): port for Redis db
    DEFAULT_REDIS_PASS (str): password for Redis db
    DEFAULT_REDIS_MEM (str): memory for launching Redis db
    DEFAULT_REDIS_CPU (str): CPUs for launching Redis db
    DEFAULT_REDIS_DIR (str): toplevel directory for Redis db storage

    DEFAULT_NGINX_PORT (int): port for nginx db
    DEFAULT_NGINX_DIR (str): toplevel directory for nginx db storage
    DEFAULT_NGINX_CONF (str): name of config path for launching nginx
"""
from argparse import ArgumentParser
import os
import re
import socket
import sys
import csv
import time
import subprocess
import shlex

print("Running on", socket.gethostname())
csvw = csv.writer(sys.stdout, delimiter='\t')
csvw.writerow(['run info', 'argv', ' '.join(map(shlex.quote, sys.argv))])
csvw.writerow(['run info', 'time', time.time()])
try:
    csvw.writerow(['run info', 'commit',
                   subprocess.check_output(['git', 'describe', '--always']).strip().decode()])
except subprocess.CalledProcessError:
    pass
except FileNotFoundError:
    pass

DEFAULT_CHRONOS_URL = 'knowcluster01.dyndns.org:8888'
DEFAULT_MARATHON_URL = 'knowcluster01.dyndns.org:8080/v2/apps'
DEFAULT_WORKING_DIR = '/workspace/prototype'

DEFAULT_CODE_PATH = 'KnowNet_Pipeline/code'
DEFAULT_DATA_PATH = 'data'
DEFAULT_LOGS_PATH = 'logs'
DEFAULT_SRC_PATH = 'srcClass'
DEFAULT_MAP_PATH = 'id_map'

DEFAULT_MYSQL_URL = 'knowice.cs.illinois.edu'
DEFAULT_MYSQL_PORT = '3306'
DEFAULT_MYSQL_USER = 'root'
DEFAULT_MYSQL_PASS = 'KnowEnG'
DEFAULT_MYSQL_MEM = '15000'
DEFAULT_MYSQL_CPU = '4.0'
DEFAULT_MYSQL_DIR = os.path.join(DEFAULT_WORKING_DIR, 'p1_mysql')
DEFAULT_MYSQL_CONF = 'build_conf/'

DEFAULT_REDIS_URL = 'knowice.cs.illinois.edu'
DEFAULT_REDIS_PORT = '6379'
DEFAULT_REDIS_PASS = 'KnowEnG'
DEFAULT_REDIS_MEM = '15000'
DEFAULT_REDIS_CPU = '1.0'
DEFAULT_REDIS_DIR = os.path.join(DEFAULT_WORKING_DIR, 'p1_redis')

DEFAULT_NGINX_PORT = '8080'
DEFAULT_NGINX_DIR = os.path.join(DEFAULT_WORKING_DIR, 'p1_nginx')
DEFAULT_NGINX_CONF = 'autoindex/'

DEFAULT_S3_BUCKET = 'KNsample'


def add_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --chronos  	    |str	|-c	    |url of chronos scheduler or LOCAL or DOCKER
    --working_dir	    |str	|-wd	|name of toplevel directory of working dir
    --storage_dir    |str	|-sd	|name of toplevel directory of shared storage
    --code_path	    |str	|-cp	|relative path of code directory from toplevel
    --data_path	    |str	|-dp	|relative path of data directory from toplevel
    --logs_path	    |str	|-lp	|relative path of data directory from toplevel
    --src_path 	    |str	|-sp	|relative path of source code directory from code directory
    --mysql_host	|str	|-myh	|url of mySQL db
    --mysql_port	|str	|-myp	|port for mySQL db
    --mysql_user	|str	|-myu	|user for mySQL db
    --mysql_pass	|str	|-myps	|password for mySQL db
    --mysql_mem     |str    |-mym   |memory for deploying MySQL container
    --mysql_cpu     |str    |-myc   |cpus for deploying MySQL container
    --mysql_dir     |str    |-myd   |directory for deploying MySQL container
    --mysql_curl    |str    |-mycu  |constraint url for deploying MySQL container
    --mysql_dir     |str    |-myd   |directory for deploying MySQL container
    --mysql_curl    |str    |-mycu  |constraint url for deploying MySQL container
    --mysql_conf    |str    |-mycf  |config directory for deploying MySQL container
    --redis_host	|str	|-rh 	|url of Redis db
    --redis_port	|str	|-rp 	|port for Redis db
    --redis_pass	|str	|-rps	|password for Redis db
    --redis_mem     |str    |-rm    |memory for deploying redis container
    --redis_cpu     |str    |-rc    |cpus for deploying redis container
    --redis_dir     |str    |-rd    |directory for deploying redis container
    --redis_curl    |str    |-rcu   |constraint url for deploying redis container
    --nginx_port	|str	|-ngp	|port for nginx db
    --nginx_dir     |str    |-ngd   |directory for deploying MySQL container
    --nginx_conf    |str    |-ngcf  |config directory for deploying nginx container
    --chunk_size	|int	|-cs	|lines per chunk
    --test_mode	    |   	|-tm	|run in test mode by only printing command, defaults to False
    --ens_species   |str    |-es    |',,' separated ensembl species to run in setup pipeline
    --force_fetch   |	    |-ff	|fetch even if file exists and has not changed from last run
    --bucket|str|-b|S3 bucket to sync output



    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-c', '--chronos', default=DEFAULT_CHRONOS_URL,
                        help='url of chronos scheduler or LOCAL or DOCKER')
    parser.add_argument('-m', '--marathon', default=DEFAULT_MARATHON_URL,
                        help='url of marathon scheduler')
    parser.add_argument('-wd', '--working_dir', default=DEFAULT_WORKING_DIR,
                        help='name of toplevel directory of working directory')
    parser.add_argument('-sd', '--storage_dir', default='', nargs='?',
                        help='name of toplevel directory of storage directory')
    parser.add_argument('-cp', '--code_path', default=DEFAULT_CODE_PATH,
                        help='relative path of code directory from toplevel')
    parser.add_argument('-dp', '--data_path', default=DEFAULT_DATA_PATH,
                        help='relative path of data directory from toplevel')
    parser.add_argument('-lp', '--logs_path', default=DEFAULT_LOGS_PATH,
                        help='relative path of data directory from toplevel')
    parser.add_argument('-sp', '--src_path', default=DEFAULT_SRC_PATH,
                        help=('relative path of source code directory from code'
                              ' directory'))
    parser.add_argument('-myh', '--mysql_host', default=DEFAULT_MYSQL_URL,
                        help='url of mySQL db')
    parser.add_argument('-myp', '--mysql_port', default=DEFAULT_MYSQL_PORT,
                        help='port for mySQL db')
    parser.add_argument('-myu', '--mysql_user', default=DEFAULT_MYSQL_USER,
                        help='user for mySQL db')
    parser.add_argument('-myps', '--mysql_pass', default=DEFAULT_MYSQL_PASS,
                        help='password for mySQL db')
    parser.add_argument('-mym', '--mysql_mem', default=DEFAULT_MYSQL_MEM,
                        help='memory for deploying MySQL container')
    parser.add_argument('-myc', '--mysql_cpu', default=DEFAULT_MYSQL_CPU,
                        help='cpus for deploying MySQL container')
    parser.add_argument('-mycu', '--mysql_curl', default='', nargs='?',
                        help='constrain url for deploying MySQL container')
    parser.add_argument('-myd', '--mysql_dir', default=DEFAULT_MYSQL_DIR,
                        help='directory for deploying MySQL container')
    parser.add_argument('-mycf', '--mysql_conf', default=DEFAULT_MYSQL_CONF,
                        help='config directory for deploying MySQL container')
    parser.add_argument('-rh', '--redis_host', default=DEFAULT_REDIS_URL,
                        help='url of Redis db')
    parser.add_argument('-rp', '--redis_port', default=DEFAULT_REDIS_PORT,
                        help='port for Redis db')
    parser.add_argument('-rps', '--redis_pass', default=DEFAULT_REDIS_PASS,
                        help='password for Redis db')
    parser.add_argument('-rm', '--redis_mem', default=DEFAULT_REDIS_MEM,
                        help='memory for deploying redis container')
    parser.add_argument('-rc', '--redis_cpu', default=DEFAULT_REDIS_CPU,
                        help='cpus for deploying redis container')
    parser.add_argument('-rcu', '--redis_curl', default='', nargs='?',
                        help='constrain url for deploying redis container')
    parser.add_argument('-rd', '--redis_dir', default=DEFAULT_REDIS_DIR,
                        help='directory for deploying redis container')
    parser.add_argument('-ngp', '--nginx_port', default=DEFAULT_NGINX_PORT,
                        help='port for nginx db')
    parser.add_argument('-ngd', '--nginx_dir', default=DEFAULT_NGINX_DIR,
                        help='directory for deploying nginx container')
    parser.add_argument('-ngcf', '--nginx_conf', default=DEFAULT_NGINX_CONF,
                        help='config directory for deploying nginx container')
    parser.add_argument('-ncu', '--nginx_curl', default='', nargs='?',
                        help='constrain url for deploying nginx container')
    parser.add_argument('-tm', '--test_mode', action='store_true', default=False,
                        help='run in test mode by only printing commands')
    parser.add_argument('-es', '--ens_species', default='REPRESENTATIVE',
                        help=',, separated list of ensembl species to run in setup pipeline')
    parser.add_argument('-ff', '--force_fetch', action='store_true', default=False,
                        help='fetch even if file exists and has not changed from last run')
    parser.add_argument('-b', '--bucket', default=DEFAULT_S3_BUCKET,
                        help='S3 bucket to sync output')

    return parser


def config_args():
    """Create a default parser with option defaults

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser = add_config_args(parser)
    args = parser.parse_args('')
    return args

def pretty_name(orig_name, endlen=63):
    """Shortens names strs and removes problematic characters

    Args:
        orig_name (str): name string before conversion
        endlen (int): max length of final pretty string

    Returns:
        str: string after formatting changes
    """
    orig_name = re.sub('[^a-zA-Z0-9]', '_', orig_name)
    return orig_name[0:endlen].upper()
