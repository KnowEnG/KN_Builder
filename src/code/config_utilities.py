"""config module to manage global variables

This module establishes default values and argument parsers for commonly
used variables

Contains module functions::

    add_run_config_args(parser)
    add_file_config_args(parser)
    add_mysql_config_args(parser)
    add_redis_config_args(parser)
    add_config_args(parser)
    config_args()
    pretty_name(orig_name, endlen=63)

Attributes:

    Default values for different configuration options
"""
from argparse import ArgumentParser
import os
import re
import socket
import sys
import csv
import time
import shlex

print("Running on", socket.gethostname())
CSVM = csv.writer(sys.stdout, delimiter='\t')
CSVM.writerow(['run info', 'argv', ' '.join(map(shlex.quote, sys.argv))])
CSVM.writerow(['run info', 'time', time.strftime("%y/%m/%d %H:%M:%S")])


DEFAULT_CHRONOS_URL = '127.0.0.1:8888'
DEFAULT_MARATHON_URL = '127.0.0.1:8080'
DEFAULT_BUILD_IMAGE = 'knoweng/kn_builder:latest'
DEFAULT_ENS_SPECIES = 'homo_sapiens'

def add_run_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --chronos       |str    |-c     |url of chronos scheduler or LOCAL or DOCKER
    --marathon      |str    |-m     |url of marathon scheduler
    --build_image   |str    |-i     |docker image name to use for kn_build pipeline
    --ens_species   |str    |-es    |',,' separated ensembl species to run in setup pipeline
    --src_classes   |str    |-srcs  |',,' separated source keywords to run in parse pipeline
    --force_fetch   |bool   |-ff    |fetch even if file exists and is unchanged from last run
    --test_mode     |bool   |-tm    |run in test mode by only printing commands

    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-c', '--chronos', default=DEFAULT_CHRONOS_URL,
                        help='url of chronos scheduler or LOCAL or DOCKER')
    parser.add_argument('-m', '--marathon', default=DEFAULT_MARATHON_URL,
                        help='url of marathon scheduler')
    parser.add_argument('-i', '--build_image', default=DEFAULT_BUILD_IMAGE,
                        help='docker image name to use for kn_build pipeline')
    parser.add_argument('-es', '--ens_species', default=DEFAULT_ENS_SPECIES,
                        help=',, separated list of ensembl species to run in setup pipeline')
    parser.add_argument('-srcs', '--src_classes', default='',
                        help=',, separated list of source keywords to run in parse pipeline')
    parser.add_argument('-ff', '--force_fetch', action='store_true', default=False,
                        help='fetch even if file exists and has not changed from last run')
    parser.add_argument('-tm', '--test_mode', action='store_true', default=False,
                        help='run in test mode by only printing commands')
    return parser


DEFAULT_WORKING_DIR = os.path.abspath('.')
DEFAULT_CODE_PATH = '/kn_builder/code/'
DEFAULT_DATA_PATH = 'data'
DEFAULT_LOGS_PATH = 'logs'
DEFAULT_EXPORT_PATH = 'userKN'
DEFAULT_SRC_PATH = 'srcClass'
DEFAULT_MAP_PATH = 'id_map' # not parameter

def add_file_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --working_dir   |str    |-wd    |absolute path to toplevel working directory
    --code_path     |str    |-cp    |absolute path of code directory
    --storage_dir   |str    |-sd    |absolute path to toplevel shared storage directory
    --data_path     |str    |-dp    |relative path of data directory from toplevel
    --logs_path     |str    |-lp    |relative path of logs directory from toplevel
    --export_path   |str    |-ep    |relative path of export directory from toplevel
    --src_path      |str    |-sp    |relative path of srcClass directory from code_path

    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-wd', '--working_dir', default=DEFAULT_WORKING_DIR,
                        help='absolute path to toplevel working directory')
    parser.add_argument('-cp', '--code_path', default=DEFAULT_CODE_PATH,
                        help='absolute path of code directory')
    parser.add_argument('-sd', '--storage_dir', default='', nargs='?',
                        help='name of toplevel directory of storage directory')
    parser.add_argument('-dp', '--data_path', default=DEFAULT_DATA_PATH,
                        help='relative path of data directory from toplevel')
    parser.add_argument('-lp', '--logs_path', default=DEFAULT_LOGS_PATH,
                        help='relative path of data directory from toplevel')
    parser.add_argument('-ep', '--export_path', default=DEFAULT_EXPORT_PATH,
                        help='relative path of export directory from toplevel')
    parser.add_argument('-sp', '--src_path', default=DEFAULT_SRC_PATH,
                        help=('relative path of srcClass directory from code_path'))
    return parser


DEFAULT_MYSQL_URL = '127.0.0.1'
DEFAULT_MYSQL_PORT = '3306'
DEFAULT_MYSQL_DIR = os.path.join(DEFAULT_WORKING_DIR, 'kn-mysql')
DEFAULT_MYSQL_MEM = '0'
DEFAULT_MYSQL_CPU = '0.5'
DEFAULT_MYSQL_CONF = 'build_conf/'
DEFAULT_MYSQL_USER = 'root'
DEFAULT_MYSQL_PASS = 'KnowEnG'

def add_mysql_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --mysql_host    |str    |-myh   |address of mySQL db
    --mysql_port    |str    |-myp   |port for mySQL db
    --mysql_dir     |str    |-myd   |absolute directory for MySQL db files
    --mysql_mem     |str    |-mym   |memory for deploying MySQL container
    --mysql_cpu     |str    |-myc   |cpus for deploying MySQL container
    --mysql_conf    |str    |-mycf  |relative config dir for deploying MySQL
    --mysql_user    |str    |-myu   |user for mySQL db
    --mysql_pass    |str    |-myps  |password for mySQL db

    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-myh', '--mysql_host', default=DEFAULT_MYSQL_URL,
                        help='address of mySQL db')
    parser.add_argument('-myp', '--mysql_port', default=DEFAULT_MYSQL_PORT,
                        help='port for mySQL db')
    parser.add_argument('-myd', '--mysql_dir', default=DEFAULT_MYSQL_DIR,
                        help='absolute directory for MySQL db files')
    parser.add_argument('-mym', '--mysql_mem', default=DEFAULT_MYSQL_MEM,
                        help='memory for deploying MySQL container')
    parser.add_argument('-myc', '--mysql_cpu', default=DEFAULT_MYSQL_CPU,
                        help='cpus for deploying MySQL container')
    parser.add_argument('-mycf', '--mysql_conf', default=DEFAULT_MYSQL_CONF,
                        help='config directory for deploying MySQL container')
    parser.add_argument('-myu', '--mysql_user', default=DEFAULT_MYSQL_USER,
                        help='user for mySQL db')
    parser.add_argument('-myps', '--mysql_pass', default=DEFAULT_MYSQL_PASS,
                        help='password for mySQL db')
    return parser


DEFAULT_REDIS_URL = '127.0.0.1'
DEFAULT_REDIS_PORT = '6379'
DEFAULT_REDIS_DIR = os.path.join(DEFAULT_WORKING_DIR, 'kn-redis')
DEFAULT_REDIS_MEM = '0'
DEFAULT_REDIS_CPU = '0.5'
DEFAULT_REDIS_PASS = 'KnowEnG'

def add_redis_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --redis_host    |str    |-rh    |address of Redis db
    --redis_port    |str    |-rp    |port for Redis db
    --redis_dir     |str    |-rd    |absolute directory for Redis db files
    --redis_mem     |str    |-rm    |memory for deploying redis container
    --redis_cpu     |str    |-rc    |cpus for deploying redis container
    --redis_pass    |str    |-rps   |password for Redis db

    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-rh', '--redis_host', default=DEFAULT_REDIS_URL,
                        help='address of Redis db')
    parser.add_argument('-rp', '--redis_port', default=DEFAULT_REDIS_PORT,
                        help='port for Redis db')
    parser.add_argument('-rd', '--redis_dir', default=DEFAULT_REDIS_DIR,
                        help='absolute directory for Redis db files')
    parser.add_argument('-rm', '--redis_mem', default=DEFAULT_REDIS_MEM,
                        help='memory for deploying redis container')
    parser.add_argument('-rc', '--redis_cpu', default=DEFAULT_REDIS_CPU,
                        help='cpus for deploying redis container')
    parser.add_argument('-rps', '--redis_pass', default=DEFAULT_REDIS_PASS,
                        help='password for Redis db')
    return parser


def add_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    group1 = parser.add_argument_group('run arguments')
    group1 = add_run_config_args(group1)
    group2 = parser.add_argument_group('path arguments')
    group2 = add_file_config_args(group2)
    group3 = parser.add_argument_group('mysql arguments')
    group3 = add_mysql_config_args(group3)
    group4 = parser.add_argument_group('redis arguments')
    group4 = add_redis_config_args(group4)
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
