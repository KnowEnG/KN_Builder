"""Place to store global variables

Classes:

Functions:

Variables:
    DEFAULT_DOCKER_IMG: docker image to run pipeline steps
    DEFAULT_CURL_URL: address of chronos scheduler
    DEFAULT_CLOUD_BASE: toplevel directory on shared cloud storage
    
    DEFAULT_LOCAL_BASE: toplevel directory on local machine
    DEFAULT_CODE_PATH: relative path of code dir from toplevel
    DEFAULT_DATA_PATH: relative path of data dir from toplevel    

"""

DEFAULT_DOCKER_IMG = 'cblatti3/python3:0.1'
DEFAULT_CURL_URL = 'mmaster02.cse.illinois.edu:4400'
DEFAULT_LOCAL_BASE = '/shared/'
DEFAULT_CLOUD_BASE = '/mnt/storage/blatti/apps/P1_source_check/'

DEFAULT_CODE_PATH = 'code'
DEFAULT_DATA_PATH = 'data'