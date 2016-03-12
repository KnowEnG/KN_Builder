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
    SPECIAL_MODES (list): list of modes that run breadth first

Examples:
    To view all optional arguments that can be specified::

        $ python3 code/setup_utilities.py -h

    To run just check step of setup locally::

        $ python3 code/setup_utilities.py CHECK STEP SETUP -c LOCAL

    To run just fetch step of setup locally after completed check::

        $ python3 code/setup_utilities.py FETCH STEP SETUP -c LOCAL

    To run all steps of setup on cloud::

        $ python3 code/setup_utilities.py CHECK PIPELINE SETUP
"""

import os
import sys
import json
from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as db
import job_utilities as jb

DEFAULT_PIPELINE_STAGE = 'SETUP'
DEFAULT_START_STEP = 'CHECK'
DEFAULT_RUN_MODE = 'STEP'
POSSIBLE_STEPS = ['CHECK', 'FETCH', 'TABLE', 'MAP']
SETUP_FILES = ['species', 'ppi', 'ensembl']
SPECIAL_MODES = ['LOCAL', 'DOCKER']

def main_parse_args():
    """Processes command line arguments.

    Expects three positional arguments(start_step, run_mode, pipeline_stage) and
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
    parser.add_argument('pipeline_stage', default=DEFAULT_PIPELINE_STAGE,
                        help='select pipeline stage, must be SETUP or PIPELINE')
    parser.add_argument('-p', '--step_parameters', default='',
                        help='parameters needed for single call of step in pipeline')
    parser.add_argument('-ne', '--no_ensembl', action='store_true', default=False,
                        help='do not run ensembl in pipeline', )
    parser.add_argument('-tm', '--testmode', action='store_true', default=False,
                        help='specifies to run things in testmode')
    parser.add_argument('-d', '--dependencies', default='',
                        help='names of job parents')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()

    config_opts = sys.argv[1:]
    for opt in [args.pipeline_stage, args.start_step, args.run_mode, '-ne', '--no_ensembl', '-tm',
                '--testmode', '-p', '--step_parameters', args.step_parameters,
                '-d', '--dependencies', args.dependencies]:
        if opt in config_opts:
            config_opts.remove(opt)
    args.config_opts = " ".join(config_opts)
    args.cloud_config_opts = args.config_opts
    if args.chronos != 'LOCAL':
        args.cloud_config_opts = cf.cloud_config_opts(args, config_opts)
    return args

def list_sources(args):
    """ creates a list of all sources for step to process

    Depending on args.pipeline_stage, loops through all sources in the srccode
    directory pulling out valid names or return SETUP_FILES

    Args:
        args (Namespace): args as populated namespace from parse_args
    """
    src_list = []
    if args.step_parameters is "":
        if args.pipeline_stage == 'PIPELINE':
            local_src_code_dir = os.path.join(args.local_dir, args.code_path,
                                              args.src_path)
            if not os.path.exists(local_src_code_dir):
                print("ERROR: cannot find {0}!".format(local_src_code_dir))
                return -1
            src_pys_list = sorted(os.listdir(local_src_code_dir))
            for filename in src_pys_list:
                if not filename.endswith(".py"):
                    continue
                if 'utilities' in filename:
                    continue
                srcstr = os.path.splitext(filename)[0]
                if srcstr in SETUP_FILES:
                    continue
                src_list.extend([srcstr])
        else: ## args.pipeline_stage == 'SETUP'
            for srcstr in SETUP_FILES:
                if srcstr is 'ensembl' and args.no_ensembl:
                    continue
                src_list.extend([srcstr])
    else:
        src_list = args.step_parameters.split(",,")
    return sorted(src_list)



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
    src_list = list_sources(args)
    ns_parameters = []
    ns_dict = {'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path)
              }
    launchstr = '"schedule": "R1\/\/P3M"'
    if args.dependencies is not "":
        launchstr = jb.chronos_parent_str(args.dependencies.split(",,"))

    for module in src_list:

        ctr += 1
        print(str(ctr) + "\t" + module)

        jobname = "-".join([args.pipeline_stage, "check", module])
        jobname = jobname.replace(".", "-")
        jobdict = {'TMPJOB': jobname,
                   'TMPLAUNCH': launchstr,
                   'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                   'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                   'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                   'TMPSRC': module,
                   'TMPOPTS': args.cloud_config_opts
                  }
        check_job = jb.run_job_step(args, "checker", jobdict)

        ns_parameters.extend([module])
        ns_jobname = "-".join([jobname, "next_step"])
        ns_dict.update({'TMPJOB': ns_jobname,
                        'TMPLAUNCH': jb.chronos_parent_str([check_job.jobname]),
                        'TMPNEXTSTEP': "FETCH",
                        'TMPSTART': module,
                        'TMPOPTS': " ".join([args.run_mode, args.pipeline_stage,
                                            args.cloud_config_opts, '-d', ns_jobname])
                       })

        if args.run_mode == "PIPELINE" and args.chronos not in SPECIAL_MODES:
            jb.run_job_step(args, "next_step_caller", ns_dict)

    if args.run_mode == "PIPELINE" and args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict.update({'TMPJOB': "-".join([args.pipeline_stage, "check", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters)
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        jb.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0

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
    src_list = list_sources(args)
    ns_parameters = []
    ns_dict = {'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path)
              }

    for src in src_list:
        local_src_dir = os.path.join(args.local_dir, args.data_path, src)
        if not os.path.exists(local_src_dir):
            print("ERROR: source specified with --step_parameters (-p) option, \
                {0}, does not have data directory: {1}".format(src, local_src_dir))
            return -1

        alias_ctr = 0

        if args.chronos not in SPECIAL_MODES:
            for alias in sorted(os.listdir(local_src_dir)):
                jobname = "-".join([args.pipeline_stage, "fetch", src, alias])
                jobname = jobname.replace(".", "-")
                jobdict = {'TMPJOB': jobname,
                           'TMPLAUNCH': '"schedule": "R1\/2200-01-01T06:00:00Z\/P3M"',
                           'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                          }
                fetch_job = jb.run_job_step(args, "placeholder", jobdict)

        for alias in sorted(os.listdir(local_src_dir)):

            alias_path = os.path.join(src, alias)
            alias_ctr += 1
            print("\t".join([src, str(alias_ctr), alias]))


            ## check for dependencies
            parents = []
            if args.dependencies is not "":
                parents = args.dependencies.split(",,")
            version_dict = {}
            with open("file_metadata.json", 'r') as infile:
                version_dict = json.load(infile)
            dependencies = version_dict["dependencies"]
            if len(dependencies) > 0:
                for dep in dependencies:
                    parent_string = "-".join([args.pipeline_stage, "fetch", src, dep])
                    parents.extend([parent_string])

            launchstr = '"schedule": "R1\/\/P3M"'
            if len(parents) > 0:
                launchstr = jb.chronos_parent_str(parents)

            jobname = "-".join([args.pipeline_stage, "fetch", src, alias])
            jobname = jobname.replace(".", "-")
            jobdict = {'TMPJOB': jobname,
                       'TMPLAUNCH': launchstr,
                       'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                       'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                       'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                       'TMPALIASDIR': alias_path,
                       'TMPOPTS': args.config_opts
                      }
            fetch_job = jb.run_job_step(args, "fetcher", jobdict)

            ns_parameters.extend([",".join([src, alias])])
            ns_jobname = "-".join([jobname, "next_step"])
            ns_dict.update({'TMPJOB': ns_jobname,
                            'TMPLAUNCH': jb.chronos_parent_str([fetch_job.jobname]),
                            'TMPNEXTSTEP': "TABLE",
                            'TMPSTART': ",".join([src, alias]),
                            'TMPOPTS': " ".join([args.run_mode, args.pipeline_stage,
                                                 args.cloud_config_opts, '-d', ns_jobname])
                           })

            if args.pipeline_stage == 'PIPELINE' and args.run_mode == "PIPELINE" and \
                args.chronos not in SPECIAL_MODES:
                jb.run_job_step(args, "next_step_caller", ns_dict)

    if args.pipeline_stage == 'PIPELINE' and args.run_mode == "PIPELINE" and \
        args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict.update({'TMPJOB': "-".join([args.pipeline_stage, "fetch", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters)
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        jb.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0

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

    if args.dependencies is "":

        if args.pipeline_stage == 'SETUP':
            knownet = db.MySQL(None, args)
            knownet.init_knownet()

        jobdict = {'TMPJOB': "file_setup_job",
                   'TMPLAUNCH': '"schedule": "R1\/\/P3M"',
                   'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                   'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                   'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path)
                  }
        file_setup_job = jb.run_job_step(args, "file_setup", jobdict)
        args.dependencies = file_setup_job.jobname

    if args.pipeline_stage == 'SETUP':
        if args.start_step == 'CHECK':
            run_check(args)
        elif args.start_step == 'FETCH':
            run_fetch(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be \
                ' + str(POSSIBLE_STEPS))
            return
    elif args.pipeline_stage == 'PIPELINE':
        if args.start_step == 'CHECK':
            run_check(args)
        elif args.start_step == 'FETCH':
            run_fetch(args)
        elif args.start_step == 'TABLE':
#            run_table(args)
            pass
        elif args.start_step == 'MAP':
#            run_map(args)
            pass
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be \
                ' + str(POSSIBLE_STEPS))
            return
    else:
        print(args.pipeline_stage + ' is an unacceptable pipeline_stage. ' +
              ' Must be SETUP or PIPELINE')
        return
    return


if __name__ == "__main__":
    main()
