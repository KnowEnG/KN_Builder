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

    DEFAULT_REDIS_URL = location of Redis db
    DEFAULT_REDIS_PORT = port for Redis db
"""
from argparse import ArgumentParser
import os
import re

DEFAULT_DOCKER_IMG = 'cblatti3/py3_redis_mysql:0.1'
DEFAULT_CURL_URL = 'mmaster01.cse.illinois.edu:4400'
DEFAULT_LOCAL_BASE = '/workspace/prototype/KnowNet_Pipeline'
DEFAULT_CLOUD_BASE = '/storage-pool/blatti/KnowNet_Pipeline'

DEFAULT_CODE_PATH = 'code'
DEFAULT_DATA_PATH = 'data'
DEFAULT_SRC_PATH = 'srcClass'
DEFAULT_MAP_PATH = 'id_map'

DEFAULT_MYSQL_URL = 'knowice.cs.illinois.edu'
DEFAULT_MYSQL_PORT = '3306'
DEFAULT_MYSQL_USER = 'root'
DEFAULT_MYSQL_PASS = 'KnowEnG'

DEFAULT_REDIS_URL = 'knowice.cs.illinois.edu'
DEFAULT_REDIS_PORT = '6379'

def add_config_args(parser):
    """Add configuation options to command line arguments.

    If argument is missing, supplies default value.

    Args:
        parser: a parser to add config opts to

    Returns: parser with appending options
    """
    parser.add_argument('-i', '--image', help='docker image name for \
        pipeline', default=DEFAULT_DOCKER_IMG)
    parser.add_argument('-c', '--chronos', help='url of chronos scheduler',
                        default=DEFAULT_CURL_URL)
    parser.add_argument('-ld', '--local_dir', help='name of toplevel directory \
        on local machine', default=DEFAULT_LOCAL_BASE)
    parser.add_argument('-cd', '--cloud_dir', help='name of toplevel directory \
        on cloud storage', default=DEFAULT_CLOUD_BASE)
    parser.add_argument('-cp', '--code_path', help='relative path of code \
        directory from toplevel ', default=DEFAULT_CODE_PATH)
    parser.add_argument('-dp', '--data_path', help='relative path of data \
        directory from toplevel', default=DEFAULT_DATA_PATH)
    parser.add_argument('-sp', '--src_path', help='relative path of source \
        code directory from code directory', default=DEFAULT_SRC_PATH)
    parser.add_argument('-myh', '--mysql_host', help='url of mySQL db',
                        default=DEFAULT_MYSQL_URL)
    parser.add_argument('-myp', '--mysql_port', help='port for mySQL db',
                        default=DEFAULT_MYSQL_PORT)
    parser.add_argument('-myu', '--mysql_user', help='user for mySQL db',
                        default=DEFAULT_MYSQL_USER)
    parser.add_argument('-myps', '--mysql_pass', help='password for mySQL db',
                        default=DEFAULT_MYSQL_PASS)
    parser.add_argument('-rh', '--redis_host', help='url of Redis db',
                        default=DEFAULT_REDIS_URL)
    parser.add_argument('-rp', '--redis_port', help='port for Redis db',
                        default=DEFAULT_REDIS_PORT)
    return parser


def config_args():
    """Create a default parser with options defaults

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser = add_config_args(parser)
    args = parser.parse_args('')
    return args

def cloud_config_opts(args, config_opts):
    """Convert config options to the directory structure within containers on cloud

    Args:
        args: args as populated namespace
        config_opts: list of command line arguments

    Returns: string for command line arguments on cloud
    """
    if '-ld' not in config_opts:
        config_opts.extend(['-ld', os.sep])
    new_config_opts = [opt.replace(args.local_dir, os.sep) for opt in config_opts]
    return " ".join(new_config_opts)

def cloud_template_subs(args, job_str):
    """Convert tmp values in template json job string to config options

    Args:
        args: args as populated namespace
        job_str: json job as string with tmp placeholder values

    Returns: json job as string with cloud tmp values replaced
    """

    job_str = job_str.replace("TMPIMG", args.image)
    job_str = job_str.replace("TMPDATADIR", os.path.join(args.cloud_dir, args.data_path))
    job_str = job_str.replace("TMPCODEDIR", os.path.join(args.cloud_dir, args.code_path))
    job_str = job_str.replace("TMPDATAPATH", args.data_path)
    job_str = job_str.replace("TMPCODEPATH", args.code_path)
    job_str = job_str.replace("TMPOPTS", args.cloud_config_opts)

    return job_str

def pretty_name(orig_name, endlen = 35):
    """Shortens names strs and removes problematic characters

    Args:
        orig_name (string): name string before conversion
        endlen (int): max length of final pretty string

    Returns: string after formatting changes
    """
    orig_name = re.sub('[^a-zA-Z0-9]','_',orig_name)
    return orig_name[0:endlen]