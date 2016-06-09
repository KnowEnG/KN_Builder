"""config module to manage global variables

This module establishes default values and argument parsers for commonly
used variables

Attributes:
    DEFAULT_CHRONOS_URL (str): address of chronos scheduler
    DEFAULT_LOCAL_BASE (str): toplevel directory on local machine
    DEFAULT_CLOUD_BASE (str): toplevel directory on shared cloud storage

    DEFAULT_CODE_PATH (str): relative path of code dir from toplevel
    DEFAULT_DATA_PATH (str): relative path of data dir from toplevel
    DEFAULT_LOGS_PATH (str): relative path of logs dir from toplevel
    DEFAULT_MAP_PATH (str): relative path of id_map dir from toplevel

    DEFAULT_MYSQL_URL (str): location of MySQL db
    DEFAULT_MYSQL_PORT (int): port for MySQL db
    DEFAULT_MYSQL_USER (str): user for MySQL db
    DEFAULT_MYSQL_PASS (str): password for MySQL db

    DEFAULT_REDIS_URL (str): location of Redis db
    DEFAULT_REDIS_PORT (int): port for Redis db
    DEFAULT_REDIS_PASS (str): password for Redis db
"""
from argparse import ArgumentParser
import os
import re

DEFAULT_CHRONOS_URL = 'knowcluster01.dyndns.org:8888'
DEFAULT_LOCAL_BASE = '/workspace/prototype/KnowNet_Pipeline'
DEFAULT_CLOUD_BASE = '/storage-pool/blatti/KnowNet_Pipeline'

DEFAULT_CODE_PATH = 'code'
DEFAULT_DATA_PATH = 'data'
DEFAULT_LOGS_PATH = 'logs'
DEFAULT_SRC_PATH = 'srcClass'
DEFAULT_MAP_PATH = 'id_map'

DEFAULT_MYSQL_URL = 'knowice.cs.illinois.edu'
DEFAULT_MYSQL_PORT = '3306'
DEFAULT_MYSQL_USER = 'root'
DEFAULT_MYSQL_PASS = 'KnowEnG'

DEFAULT_REDIS_URL = 'knowice.cs.illinois.edu'
DEFAULT_REDIS_PORT = '6379'
DEFAULT_REDIS_PASS = 'KnowEnG'

def add_config_args(parser):
    """Add global configuation options to command line arguments.

    If global arguments are not specified, supplies their default values.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    --chronos  	    |str	|-c	    |url of chronos scheduler or LOCAL or DOCKER
    --local_dir	    |str	|-ld	|name of toplevel directory on local machine
    --cloud_dir	    |str	|-cd	|name of toplevel directory on cloud storage
    --shared_dir    |str	|-sd	|name of toplevel directory of shared storage
    --code_path	    |str	|-cp	|relative path of code directory from toplevel
    --data_path	    |str	|-dp	|relative path of data directory from toplevel
    --logs_path	    |str	|-lp	|relative path of data directory from toplevel
    --src_path 	    |str	|-sp	|relative path of source code directory from code directory
    --mysql_host	|str	|-myh	|url of mySQL db
    --mysql_port	|int	|-myp	|port for mySQL db
    --mysql_user	|str	|-myu	|user for mySQL db
    --mysql_pass	|str	|-myps	|password for mySQL db
    --redis_host	|str	|-rh 	|url of Redis db
    --redis_port	|int	|-rp 	|port for Redis db
    --redis_pass	|str	|-rps	|password for Redis db
    --chunk_size	|int	|-cs	|lines per chunk
    --test_mode	    |   	|-tm	|run in test mode by only printing command, defaults to False
    --ens_species   |str    |-es    |',,' separated ensembl species to run in setup pipeline
    --force_fetch   |	    |-ff	|fetch even if file exists and has not changed from last run



    Args:
        parser (argparse.ArgumentParser): a parser to add global config opts to

    Returns:
        argparse.ArgumentParser: parser with appended global options
    """
    parser.add_argument('-c', '--chronos', default=DEFAULT_CHRONOS_URL,
                        help='url of chronos scheduler or LOCAL or DOCKER')
    parser.add_argument('-ld', '--local_dir', default=DEFAULT_LOCAL_BASE,
                        help='name of toplevel directory on local machine')
    parser.add_argument('-cd', '--cloud_dir', default=DEFAULT_CLOUD_BASE,
                        help='name of toplevel directory on cloud storage')
    parser.add_argument('-sd', '--shared_dir', default='',
                        help='name of toplevel directory on shared storage')
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
    parser.add_argument('-rh', '--redis_host', default=DEFAULT_REDIS_URL,
                        help='url of Redis db')
    parser.add_argument('-rp', '--redis_port', default=DEFAULT_REDIS_PORT,
                        help='port for Redis db')
    parser.add_argument('-rps', '--redis_pass', default=DEFAULT_REDIS_PASS,
                        help='password for Redis db')
    parser.add_argument('-tm', '--test_mode', action='store_true', default=False,
                        help='run in test mode by only printing commands')
    parser.add_argument('-es', '--ens_species', default='REPRESENTATIVE',
                        help=',, separated list of ensembl species to run in setup pipeline' )
    parser.add_argument('-ff', '--force_fetch', action='store_true', default=False,
                        help='fetch even if file exists and has not changed from last run', )

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

def cloud_config_opts(args, config_opts):
    """Convert config options to the directory structure within containers on cloud

    changes/appends arg.local_dir to root of container's file system

    Args:
        args (Namespace): args as populated namespace
        config_opts (list): list of command line arguments

    Returns:
        str: string for command line arguments on cloud
    """
    if '-ld' not in config_opts:
        config_opts.extend(['-ld', args.cloud_dir])
    new_config_opts = [opt.replace(args.local_dir, args.cloud_dir) for opt in config_opts]
    return " ".join(new_config_opts)

def cloud_template_subs(args, job_str):
    """Convert tmp values in template json job string to config options

    Args:
        args (Namespace): args as populated namespace
        job_str (str): json job as string with tmp placeholder values

    Returns:
        str: json job as string with cloud tmp values replaced
    """

    job_str = job_str.replace("TMPIMG", args.image)
    job_str = job_str.replace("TMPDATADIR", os.path.join(args.cloud_dir, args.data_path))
    job_str = job_str.replace("TMPCODEDIR", os.path.join(args.cloud_dir, args.code_path))
    job_str = job_str.replace("TMPDATAPATH", args.data_path)
    job_str = job_str.replace("TMPCODEPATH", args.code_path)
    job_str = job_str.replace("TMPOPTS", args.cloud_config_opts)

    return job_str

def pretty_name(orig_name, endlen=63):
    """Shortens names strs and removes problematic characters

    Args:
        orig_name (str): name string before conversion
        endlen (int): max length of final pretty string

    Returns:
        str: string after formatting changes
    """
    orig_name = re.sub('[^a-zA-Z0-9]', '_', orig_name)
    return orig_name[0:endlen]
