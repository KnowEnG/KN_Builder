#!/usr/bin/env python3
"""Utiliites for running single or multiple steps of the supermaster pipeline
        either locally or on the cloud.

Contains module functions::

    run_check(args)
    run_fetch(args)
    main_parse_args()
    main()

Attributes:
    DEFAULT_START_STEP (str): first step of setup
    DEFAULT_RUN_MODE (str): how to run setup
    POSSIBLE_STEPS (list): list of all steps
    SETUP_FILES (list): list of setup SrcClasses

Examples:
    To view all optional arguments that can be specified::

        $ python3 code/setup_utilities.py -h

    To run just check step of setup locally::

        $ python3 code/setup_utilities.py CHECK STEP -c LOCAL

    To run just fetch step of setup locally after completed check::

        $ python3 code/setup_utilities.py FETCH STEP -c LOCAL

    To run all steps of setup on cloud::

        $ python3 code/setup_utilities.py CHECK PIPELINE
"""

from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as db
import job_utilities as jb
import os
import sys
import subprocess
import json

DEFAULT_START_STEP = 'CHECK'
DEFAULT_RUN_MODE = 'STEP'
POSSIBLE_STEPS = ['CHECK', 'FETCH']
SETUP_FILES = ['species', 'ppi', 'ensembl']

def main_parse_args():
    """Processes command line arguments.

    Expects two positional arguments(start_step, run_mode) and
    a number of optional arguments. If argument is missing, supplies default
    value.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('start_step', default=DEFAULT_START_STEP,
                        help='select start step, must be CHECK or FETCH')
    parser.add_argument('run_mode', default=DEFAULT_RUN_MODE,
                        help='select run mode, must be STEP or PIPELINE')
    parser.add_argument('-p', '--step_parameters', default='',
                        help='parameters needed for single call of step in pipeline')
    parser.add_argument('-ne', '--no_ensembl', action='store_true', default=False,
                        help='do not run ensembl in pipeline', )
    parser.add_argument('-tm', '--testmode', action='store_true', default=False,
                        help='specifies to run things in testmode')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()

    config_opts = sys.argv[1:]
    for opt in [args.start_step, args.run_mode, '-ne', '--no_ensembl', '-tm',
               '--testmode', '-p', '--step_parameters', args.step_parameters]:
        if opt in config_opts:
            config_opts.remove(opt)
    args.config_opts = " ".join(config_opts)
    if args.chronos != 'LOCAL':
        args.config_opts = cf.cloud_config_opts(args, config_opts)
    return args

def run_check(args):
    """Runs checks for all sources.

    This loops through all sources in the code directory, creates a
    json chronos jobs for each source that calls check_utilities
    clean() (and if run_mode 'PIPELINE', the call to
    setup_utilities FETCH) and curls json to chronos.

    Args:
        args (Namespace): args as populated namespace from parse_args
    """
    ctr = 0
    for module in SETUP_FILES:

        if module is 'ensembl' and args.no_ensembl:
            continue

        jobname = "-".join(["check", module])
        jobname = jobname.replace(".", "-")
        pipeline_cmd = ""
        if args.run_mode == "PIPELINE":
            arg_str = " ".join([args.run_mode, args.config_opts])
            pipeline_cmd = "python3 /{0}/setup_utilities.py FETCH {1} -p {2}\
                            ;".format(os.path.join(args.cloud_dir, args.code_path),
                                      arg_str, module)

        ctr += 1
        print(str(ctr) + "\t" + module)

        tmptype = "setup_check"
        tmpdict = {'TMPJOB': jobname,
               'TMPLAUNCH': '"schedule": "R1\/\/P3M"',
               'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
               'TMPPIPECMD': pipeline_cmd,
               'TMPSRC': module,
               'TMPOPTS': args.config_opts
               }
        setup_check_job = jb.run_job_step(args, tmptype, tmpdict)

def run_fetch(args):
    """Runs fetches for all aliases of a single source.

    For a single source, this loops through all aliases in the data directory,
    creates a json chronos jobs for each alias that calls fetch_utilities
    main() (and if run_mode 'PIPELINE', the call to )
    and curls json to chronos.

    Args:
        args (Namespace): args as populated namespace from parse_args, must
            specify --step_parameters(-p) as single source
    """
    src = args.step_parameters
    if src is '':  # call fetch for all srcs
        for src_name in SETUP_FILES:
            if src_name is 'ensembl' and args.no_ensembl:
                continue
            args.step_parameters=src_name
            run_fetch(args)

    print("'source' specified with --step_parameters (-p): {0}".format(src))
    local_src_dir = os.path.join(args.local_dir, args.data_path, src)
    if not os.path.exists(local_src_dir):
        print("ERROR: source specified with --step_parameters (-p) option, \
            {0}, does not have data directory: {1}".format(src, local_src_dir))
        return -1

    ctr = 0
    for alias in sorted(os.listdir(local_src_dir)):

        alias_path = os.path.join(src, alias)
        jobname = "-".join(["fetch", src, alias])
        jobname = jobname.replace(".", "-")
        pipeline_cmd = ""
        #if src == 'ensembl':
        #    pipeline_cmd = "/usr/bin/time -v python3 /{0}/import_utilities.py \
        #                    file_metadata.json {1};".format(args.code_path,
        #                                                    args.config_opts)
        if args.run_mode == "PIPELINE":
            pass

        ctr += 1
        print("\t".join([str(ctr), src, alias]))

        tmptype = "setup_fetch"
        tmpdict = {'TMPJOB': jobname,
               'TMPLAUNCH': '"schedule": "R1\/\/P3M"',
               'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
               'TMPPIPECMD': pipeline_cmd,
               'TMPALIASPATH': alias_path,
               'TMPOPTS': args.config_opts
               }
        setup_fetch_job = jb.run_job_step(args, tmptype, tmpdict)

def main():
    """Runs the 'start_step' step of the pipeline on the local or
    cloud location, and all subsequent steps if PIPELINE 'run_mode'

    Parses the arguments and runs the specified part of the pipeline using the
    specified local or cloud resources.
    """

    args = main_parse_args()
    if not args.run_mode == 'PIPELINE' and not args.run_mode == 'STEP':
        print(args.run_mode + ' is an unacceptable run_mode.  Must be STEP or PIPELINE')
        return

    tmptype = "file_setup"
    tmpdict = {'TMPJOB': "file_setup_job",
               'TMPLAUNCH': '"schedule": "R1\/\/P3M"',
               'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path)
               }
    filesetup_job = jb.run_job_step(args, tmptype, tmpdict)

    knownet = db.MySQL(None, args)
    knownet.init_knownet()

    if args.start_step == 'CHECK':
        run_check(args)
    elif args.start_step == 'FETCH':
        run_fetch(args)
    else:
        print(args.start_step + ' is an unacceptable start_step.  Must be \
            ' + str(POSSIBLE_STEPS))
        return

    return


if __name__ == "__main__":
    main()
