#!/usr/bin/env python3
"""Utiliites for running single or multiple steps of the setup or data pipeline
        either locally , in docker, or on the cloud.

Contains module functions::

    list_sources(args)
    run_check(args)
    run_fetch(args)
    run_table(args)
    run_map(args)
    main_parse_args()
    main()

Attributes:
    DEFAULT_START_STEP (str): first step of setup
    POSSIBLE_STEPS (list): list of all steps
    SETUP_FILES (list): list of setup SrcClasses
    SPECIAL_MODES (list): list of modes that run breadth first

Examples:
    To view all optional arguments that can be specified::

        $ python3 code/workflow_utilities.py -h

    To run just check step of one setup src (e.g. ppi) locally::

        $ python3 code/workflow_utilities.py CHECK -su -os -c LOCAL -p ppi

    To run all steps of setup on cloud::

        $ python3 code/workflow_utilities.py CHECK -su

    To run all steps one pipeline src (e.g. kegg) locally::

        $ python3 code/workflow_utilities.py CHECK -os -c LOCAL -p kegg

"""

import os
import sys
import json
from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as db
import job_utilities as jb

DEFAULT_START_STEP = 'CHECK'
POSSIBLE_STEPS = ['CHECK', 'FETCH', 'TABLE', 'MAP']
SETUP_FILES = ['species', 'ppi', 'ensembl']
SPECIAL_MODES = ['LOCAL', 'DOCKER']

def main_parse_args():
    """Processes command line arguments.

    Expects one argument (start_step) and a number of optional arguments. If
    argument is missing, supplies default value.

.. csv-table::
    :header: parameter,argument,flag,description
    :widths: 4,2,2,12
    :delim: |

    [start_step]    	|	    |	    |string indicating which pipeline stage to start with
    --setup	            |	    |-su	|run db inits instead of source specific pipelines
    --one_step      	|	    |-os	|run for a single step instead of rest of pipeline
    --step_parameters	|str	|-p	    |parameters to specify calls of a single step in pipeline
    --no_ensembl	    |	    |-ne	|do not run ensembl in setup pipeline
    --dependencies	    |str	|-d	    |names of parent jobs that must finish

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('start_step', default=DEFAULT_START_STEP,
                        help='start step, must be ' + str(POSSIBLE_STEPS))
    parser.add_argument('-su', '--setup', default=False, action='store_true',
                        help='run db inits instead of source specific pipelines')
    parser.add_argument('-os', '--one_step', default=False, action='store_true',
                        help='run for a single step instead of pipeline')
    parser.add_argument('-p', '--step_parameters', default='',
                        help='parameters to specify calls of a single step in pipeline')
    parser.add_argument('-ne', '--no_ensembl', action='store_true', default=False,
                        help='do not run ensembl in setup pipeline', )
    parser.add_argument('-d', '--dependencies', default='',
                        help='names of parent jobs that must finish')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()

    config_opts = sys.argv[1:]
    for opt in [args.start_step, '-p', '--step_parameters', args.step_parameters,
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

    Depending on args.setup, loops through all sources in the srccode
    directory pulling out valid names or return SETUP_FILES

    Args:
        args (Namespace): args as populated namespace from parse_args
    """
    src_list = []
    if args.step_parameters is "":
        if args.setup:
            for srcstr in SETUP_FILES:
                if srcstr is 'ensembl' and args.no_ensembl:
                    continue
                src_list.extend([srcstr])
        else:
            local_src_code_dir = os.path.join(args.local_dir, args.code_path,
                                              args.src_path)
            if not os.path.exists(local_src_code_dir):
                raise IOError("ERROR: cannot find {0}!".format(local_src_code_dir))
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

    else:
        src_list = args.step_parameters.split(",,")
    return sorted(src_list)


def run_check(args):
    """Runs checks for all sources.

    This loops through args.parameters sources, creates a job for each that calls
    check_utilities clean() (and if not args.one_step, calls workflow_utilities
    FETCH), and runs job in args.chronos location.

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

        jobname = "-".join(["check", module])
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
                        'TMPOPTS': " ".join([args.cloud_config_opts, '-d', ns_jobname])
                       })

        if not args.one_step and args.chronos not in SPECIAL_MODES:
            jb.run_job_step(args, "next_step_caller", ns_dict)

    if not args.one_step and args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict.update({'TMPJOB': "-".join(["check", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters)
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        jb.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0


def run_fetch(args):
    """Runs fetches for all aliases of a single source.

    This loops through aliases of args.parameters sources, creates a job for
    each that calls fetch_utilities main() (and if not args.one_step, calls
    workflow_utilities TABLE), and runs job in args.chronos location.

    Args:
        args (Namespace): args as populated namespace from parse_args, must
            specify --step_parameters(-p) as ',,' separated list of sources
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
            raise IOError("ERROR: source specified with --step_parameters (-p) option, \
                {0}, does not have data directory: {1}".format(src, local_src_dir))

        alias_ctr = 0
        if args.chronos not in SPECIAL_MODES:
            for alias in sorted(os.listdir(local_src_dir)):
                jobname = "-".join(["fetch", src, alias])
                jobname = jobname.replace(".", "-")
                jobdict = {'TMPJOB': jobname,
                           'TMPLAUNCH': '"schedule": "R1\/2200-01-01T06:00:00Z\/P3M"',
                           'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                           'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                           'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                          }
                fetch_job = jb.run_job_step(args, "placeholder", jobdict)

        for alias in sorted(os.listdir(local_src_dir)):

            alias_path = os.path.join(src, alias)
            local_alias_dir = os.path.join(local_src_dir, alias)
            alias_ctr += 1
            print("\t".join([src, str(alias_ctr), alias]))

            ## check for dependencies
            parents = []
            if args.dependencies is not "":
                parents = args.dependencies.split(",,")

            metadata_file = os.path.join(local_alias_dir, "file_metadata.json")
            if not os.path.isfile(metadata_file):
                raise IOError("ERROR: Missing {0}".format(metadata_file))

            version_dict = {}
            with open(metadata_file, 'r') as infile:
                version_dict = json.load(infile)
            dependencies = version_dict["dependencies"]
            if len(dependencies) > 0:
                for dep in dependencies:
                    parent_string = "-".join(["fetch", src, dep])
                    parents.extend([parent_string])

            launchstr = '"schedule": "R1\/\/P3M"'
            if len(parents) > 0:
                launchstr = jb.chronos_parent_str(parents)

            jobname = "-".join(["fetch", src, alias])
            jobname = jobname.replace(".", "-")
            jobdict = {'TMPJOB': jobname,
                       'TMPLAUNCH': launchstr,
                       'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                       'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                       'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                       'TMPALIASDIR': alias_path,
                       'TMPOPTS': args.cloud_config_opts
                      }
            fetch_job = jb.run_job_step(args, "fetcher", jobdict)

            ns_parameters.extend([",".join([src, alias])])
            ns_jobname = "-".join([jobname, "next_step"])
            ns_dict.update({'TMPJOB': ns_jobname,
                            'TMPLAUNCH': jb.chronos_parent_str([fetch_job.jobname]),
                            'TMPNEXTSTEP': "TABLE",
                            'TMPSTART': ",".join([src, alias]),
                            'TMPOPTS': " ".join([args.cloud_config_opts, '-d', ns_jobname])
                           })

            if not args.setup and not args.one_step and args.chronos not in SPECIAL_MODES:
                jb.run_job_step(args, "next_step_caller", ns_dict)

    if not args.setup and not args.one_step and \
        args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict.update({'TMPJOB': "-".join(["fetch", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters)
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        jb.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0


def run_table(args):
    """Runs tables for all chunks of a single source alias.

    This loops through chunks of args.parameters aliases, creates a job for
    each that calls table_utilities main() (and if not args.one_step, calls
    workflow_utilities MAP), and runs job in args.chronos location.

    Args:
        args (Namespace): args as populated namespace from parse_args, must
            specify --step_parameters(-p) as ',,' separated list of
            'source,alias'
    """
    alias_list = args.step_parameters.split(",,")
    if args.step_parameters is "":
        raise ValueError("ERROR: 'source,alias' must be specified with --step_parameters (-p)")

    ns_parameters = []
    ns_dict = {'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
               'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
               'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path)
              }

    launchstr = '"schedule": "R1\/\/P3M"'
    if args.dependencies is not "":
        launchstr = jb.chronos_parent_str(args.dependencies.split(",,"))

    for pair in alias_list:
        src, alias = pair.split(",")

        alias_path = os.path.join(src, alias)
        local_chunk_dir = os.path.join(args.local_dir, args.data_path, alias_path, "chunks")
        if not os.path.exists(local_chunk_dir):
            raise IOError('ERROR: "source,alias" specified with --step_parameters '
                          '(-p) option, ' + pair + ' does not have chunk directory:'
                          + local_chunk_dir)

        chunk_ctr = 0
        for chunk_name in sorted(os.listdir(local_chunk_dir)):
            if "rawline" not in chunk_name:
                continue

            chunk_ctr += 1
            print("\t".join([str(chunk_ctr), chunk_name]))

            jobname = "-".join(["table", chunk_name])
            jobname = jobname.replace(".", "-")
            jobname = jobname.replace(".txt", "")
            jobdict = {'TMPJOB': jobname,
                       'TMPLAUNCH': launchstr,
                       'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                       'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                       'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                       'TMPALIASDIR': alias_path,
                       'TMPCHUNK': os.path.join("chunks", chunk_name),
                       'TMPOPTS': args.cloud_config_opts
                      }
            table_job = jb.run_job_step(args, "tabler", jobdict)

            ns_parameters.extend([chunk_name.replace('.rawline.', '.edge.')])
            ns_jobname = "-".join([jobname, "next_step"])
            ns_dict.update({'TMPJOB': ns_jobname,
                            'TMPLAUNCH': jb.chronos_parent_str([table_job.jobname]),
                            'TMPNEXTSTEP': "MAP",
                            'TMPSTART': chunk_name.replace('.rawline.', '.edge.'),
                            'TMPOPTS': " ".join([args.cloud_config_opts, '-d', ns_jobname])
                           })

            if not args.setup and not args.one_step and \
                args.chronos not in SPECIAL_MODES:
                jb.run_job_step(args, "next_step_caller", ns_dict)

    if not args.setup and not args.one_step and \
        args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict.update({'TMPJOB': "-".join(["table", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters)
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        jb.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0


def run_map(args):
    """Runs id conversion for a single .edge. file on the cloud.

    This loops through args.parameters edgefiles, creates a job for each that
    calls conv_utilities main(), and runs job in args.chronos location.

    Args:
        args (Namespace): args as populated namespace from parse_args, must
            specify --step_parameters(-p) as ',,' separated list of
            'source.alias.chunk.edge.txt' file names
    """
    edgefile_list = args.step_parameters.split(",,")
    if args.step_parameters is "":
        raise ValueError("ERROR: 'edgefile' must be specified with --step_parameters (-p)")

    launchstr = '"schedule": "R1\/\/P3M"'
    if args.dependencies is not "":
        launchstr = jb.chronos_parent_str(args.dependencies.split(",,"))

    ctr = 0
    for filestr in edgefile_list:

        edgefile = os.path.basename(filestr)
        src = edgefile.split('.')[0]
        alias = edgefile.split('.edge.')[0].split(src+'.')[1]

        chunk_path = os.path.join(src, alias, "chunks")
        local_chunk_dir = os.path.join(args.local_dir, args.data_path, chunk_path)
        local_edgefile = os.path.join(local_chunk_dir, edgefile)
        if not os.path.exists(local_edgefile):
            raise IOError('ERROR: "edgefile" specified with --step_parameters (-p) '
                          'option, ' + filestr + ' does not exist: ' + local_edgefile)

        ctr += 1
        print("\t".join([str(ctr), edgefile]))

        jobname = "-".join(["map", edgefile])
        jobname = jobname.replace(".", "-")
        jobname = jobname.replace(".txt", "")
        jobdict = {'TMPJOB': jobname,
                   'TMPLAUNCH': launchstr,
                   'TMPDATADIR': os.path.join(args.cloud_dir, args.data_path),
                   'TMPCODEDIR': os.path.join(args.cloud_dir, args.code_path),
                   'TMPLOGSDIR': os.path.join(args.cloud_dir, args.logs_path),
                   'TMPEDGEPATH': os.path.join(chunk_path, edgefile),
                   'TMPOPTS': args.cloud_config_opts
                  }
        jb.run_job_step(args, "mapper", jobdict)

    return 0


def main():
    """Runs the 'start_step' step of the main or args.setup pipeline on the
    args.chronos location, and all subsequent steps if not args.one_step

    Parses the arguments and runs the specified part of the pipeline using the
    specified local or cloud resources.
    """

    args = main_parse_args()
    if args.dependencies is "":

        if args.setup:
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

    if args.setup:
        if args.start_step == 'CHECK':
            return run_check(args)
        elif args.start_step == 'FETCH':
            return run_fetch(args)
    else:
        if args.start_step == 'CHECK':
            return run_check(args)
        elif args.start_step == 'FETCH':
            return run_fetch(args)
        elif args.start_step == 'TABLE':
            return run_table(args)
        elif args.start_step == 'MAP':
            return run_map(args)

    print(args.start_step + ' is an unacceptable start_step.  Must be ' +
          str(POSSIBLE_STEPS))


if __name__ == "__main__":
    main()
