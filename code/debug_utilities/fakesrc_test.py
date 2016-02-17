"""Utiliites for testing pipeline utilities with a small fake source.

Contains module functions::



Attributes:
    DEFAULT_SQL (str): SQL host name for testing db
    DEFAULT_REDIS (str): Redis host name for testing db
    DEFAULT_SRC_PATH (str): location of srcClass files
    SRC (str): name of the source to test
    ALIAS (str): name of the source alias to test
    YELLOW (str): Unicode yellow
    GREEN (str): Unincode green
    RED (str): Unicode red
    END (str): Unicode end color


Examples:
    To view all optional arguments that can be specified::

        $ python3 code/debug_utilities/fakesrc_test.py -h

    To run the testing suite::

        $ python3 code/debug_utilities/fakesrc_test.py

"""

from argparse import ArgumentParser
import os
import traceback
import urllib.request
import tarfile
import subprocess
import filecmp
import difflib
import shutil
import sys
#work around for importing from parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import config_utilities as cf
import pipeline_utilities as pu

DEFAULT_SQL = 'knowcorey.dyndns.org'
DEFAULT_REDIS = 'knowcorey.dyndns.org'
DEFAULT_SRC_PATH = os.path.join('debug_utilities', 'srcClass')
SRC = 'fake_src'
ALIAS = 'fake_alias'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
END = '\033[0m'

def main_parse_args():
    """Processes command line arguments.

    Over rides default mysql host, redis host, and source path values from
    config_utilities to the values in DEFAULT_SQL, DEFAULT_REDIS, and
    DEFAULT_SRC_PATH. Also over rides the run_mode parameter to 'LOCAL', the
    step_parameters parameter to 'fake_src', and the . Uses add_config_args from
    config_utilities to set the remaining arguemnets.

    Returns:
        Namespace: args as populated namespace
    """
    #modify system arguements
    if '-sp' not in sys.argv:
        sys.argv += ['-sp', DEFAULT_SRC_PATH]
    if '-myh' not in sys.argv:
        sys.argv += ['-myh', DEFAULT_SQL]
    if '-rh' not in sys.argv:
        sys.argv += ['-rh', DEFAULT_REDIS]

    parser = ArgumentParser()
    parser.add_argument('-ko', '--keep_files', help='If provided, keeps the \
        outputs and tesing files', action='store_true', default=False)
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    args.run_mode = 'LOCAL'
    args.step_parameters = SRC
    args.chunk_size = 5

    return args

def cleanup(outdir, testdir):
    """If present, removes the fake_src data and correct outputs from disk.

    This cleans up testing files by removing both the downloaded correct
    outputs and the processed test outputs.

    Args:
        outdir (str): path to fake_src data on disk
        testdir (str): path to testable outputs on disk
    """
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    if os.path.exists(testdir):
        shutil.rmtree(testdir)

def download_outputs(args):
    """Downloads the correct outputs to disk in order to diff the outputs

    This downloads the correct outputs for the pipeline_utilities functions
    from knowcloud and stores them in the args.local_dir/tests/ directory.

    Args:
        args (Namespace): args as populated namespace from parse_args
    """
    url = ('http://knowcloud.cse.illinois.edu/index.php/s/uUaaHc7NYvxmfZV/'
        'download')
    filename = os.path.join(args.local_dir, 'tests', 'outputs.tgz')
    with urllib.request.urlopen(url) as response:
        with open(filename, 'wb') as outfile:
            shutil.copyfileobj(response, outfile)
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall(path=os.path.join(args.local_dir, 'tests'))
    os.remove(filename)

def diff_outputs(outdir, testdir):
    """Diff the files found in outdir and testdir

    This compares all of the files in outdir and testdir and returns the diff
    of the two. If their are no differences, prints PASSED. Otherwise, it prints
    the differing lines and FAILED.

    Args:
        outdir (str): path to fake_src data on disk
        testdir (str): path to testable outputs on disk

    Returns:
    """
    diff_dirs = filecmp.dircmp(outdir, testdir).diff_files
    if not diff_dirs:
        print(GREEN + 'PASSED - outputs match expected' + END)
        return True
    else:
        for fl in diff_dirs:
            print(RED + fl + ' differs' + END)
            with open(os.path.join(outdir, fl)) as fl1, \
                open(os.path.join(testdir, fl)) as fl2:
                    diff = difflib.ndiff(fl1.readlines(), fl2.readlines())
                    print(''.join(list(diff)))
        print(RED + 'FAILED - outputs do not match expected' + END)
        return False

def main():
    """Runs the full fakesrc test.

    This parses the arguemetns, sets the input and output directories, removes
    any previous testing data, and then downloads the correct outputs. It then
    runs pipeline_utilities functions for check, fetch, table, and conv and
    diffs their outputs with the expected outputs.
    """
    args = main_parse_args()
    outdir = os.path.join(args.local_dir, args.data_path, SRC, ALIAS)
    testdir = os.path.join(args.local_dir, 'tests', SRC)
    cleanup(outdir, testdir)
    download_outputs(args)
    allpass = True
    print(YELLOW + '***TESTING LOCAL CHECK***' + END)
    pu.run_local_check(args)
    allpass = allpass and diff_outputs(outdir, os.path.join(testdir, 'check'))
    print(YELLOW + '***TESTING LOCAL FETCH***' + END)
    pu.run_local_fetch(args)
    allpass = allpass and diff_outputs(outdir, os.path.join(testdir, 'fetch'))
    print(YELLOW + '***TESTING LOCAL TABLE***' + END)
    pu.run_local_table(args)
    allpass = allpass and diff_outputs(outdir, os.path.join(testdir, 'table'))
    print(YELLOW + '***TESTING LOCAL MAP***' + END)
    pu.run_local_conv(args)
    allpass = allpass and diff_outputs(outdir, os.path.join(testdir, 'map'))
    if allpass:
        print(GREEN + 'All tests passed' + END)
    if allpass and not args.keep_files:
        cleanup(outdir, testdir)

if __name__ == '__main__':
    main()
