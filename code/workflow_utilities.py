#!/usr/bin/env python3
"""Utiliites for running single or multiple steps of the setup or data pipeline
        either locally , in docker, or on the cloud.

Contains module functions::

    list_sources(args)
    generic_dict(args, ns_parent=None)
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
import time
from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as db
import job_utilities as ju

DEFAULT_START_STEP = 'CHECK'
POSSIBLE_STEPS = ['CHECK', 'FETCH', 'TABLE', 'MAP', 'IMPORT', 'EXPORT']
SETUP_FILES = ['ppi', 'ensembl']
SPECIAL_MODES = ['LOCAL', 'DOCKER']

def main_parse_args():
    """Processes command line arguments.

    Expects one argument (start_step) and a number of optional arguments. If
    argument is missing, supplies default value.

.. csv-table::
    :header: parameter,argument type,flag,description
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
    workflow_opts = []
    for opt in ['-su', '--setup', '-os', '--one_step', '-ne', '--no_ensembl']:
        if opt in config_opts:
            config_opts.remove(opt)
            workflow_opts.extend([opt])
    args.time_stamp = time.strftime('_%m-%d_%H-%M-%S')
    args.config_opts = " ".join(config_opts)
    args.workflow_opts = " ".join(workflow_opts)
    args.working_dir = args.working_dir.rstrip('/')
    args.storage_dir = args.storage_dir.rstrip('/')
    return args


def list_sources(args):
    """ creates a list of all sources for step to process

    Depending on args.setup, loops through all sources in the srccode
    directory pulling out valid names or return SETUP_FILES

    Args:
        args (Namespace): args as populated namespace from parse_args
    """
    src_list = []
    if args.step_parameters == "":
        if args.setup:
            for srcstr in SETUP_FILES:
                if srcstr == 'ensembl' and args.no_ensembl:
                    continue
                src_list.extend([srcstr])
        else:
            local_src_code_dir = os.path.join(args.working_dir, args.code_path,
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


def generic_dict(args, ns_parent=None):
    """ Creates a dictionary to specify variables for a job

    Creates a dictionary used to substitute temporary job variables in the specification
    of the command line call. ns_parent should be defined for only a next step caller
    job.

    Args:
        args (Namespace): args as populated namespace from parse_args

    Returns:
        dict: tmp substitution dictionary with appropriate values depending on args
    """

    job_dict = {'TMPLAUNCH': r'"schedule": "R1\/\/P3M"',
                'TMPWORKDIR': args.working_dir,
                'TMPDATAPATH': args.data_path,
                'TMPCODEPATH': args.code_path,
                'TMPLOGSPATH': args.logs_path,
                'TMPOPTS': args.config_opts,
                'TMPSHAREDIR': args.storage_dir,
                'TMPSHAREBOOL': 'false'
               }
    if ns_parent is None: # regular job
        if args.dependencies != "": # continuation job
            job_dict['TMPLAUNCH'] = ju.chronos_parent_str(args.dependencies.split(",,"))
    else: # next step caller job
        job_dict['TMPLAUNCH'] = ju.chronos_parent_str([ns_parent])
    if args.storage_dir and args.storage_dir != args.working_dir:
        job_dict['TMPSHAREBOOL'] = 'true'
    else:
        job_dict['TMPSHAREDIR'] = job_dict['TMPWORKDIR']
    return job_dict

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
    step_job = ju.Job("checker", args)

    for module in src_list:

        ctr += 1
        print(str(ctr) + "\t" + module)

        jobname = "-".join(["check", module])
        jobname = jobname.replace(".", "-")
        jobdict = generic_dict(args, None)
        jobdict.update({'TMPJOB': jobname,
                        'TMPSRC': module
                       })
        step_job = ju.run_job_step(args, "checker", jobdict)

        ns_parameters.extend([module])

        if not args.one_step and args.chronos not in SPECIAL_MODES:
            ns_jobname = "-".join([jobname, "next_step"])
            ns_dict = generic_dict(args, step_job.jobname)
            ns_dict.update({'TMPJOB': ns_jobname,
                            'TMPNEXTSTEP': "FETCH",
                            'TMPSTART': module,
                            'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                                 '-d', ns_jobname])
                           })
            ju.run_job_step(args, "next_step_caller", ns_dict)

    if not args.one_step and args.chronos in SPECIAL_MODES and ns_parameters:
        ns_dict = generic_dict(args, step_job.jobname)
        ns_dict.update({'TMPJOB': "-".join(["check", "next_step"]),
                        'TMPSTART': ",,".join(ns_parameters),
                        'TMPNEXTSTEP': "FETCH",
                        'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                             '-d', "-".join(["check", "next_step"])])
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        ju.run_job_step(tmpargs, "next_step_caller", ns_dict)

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
    step_job = ju.Job("fetcher", args)

    for src in src_list:
        local_src_dir = os.path.join(args.working_dir, args.data_path, src)
        if not os.path.exists(local_src_dir):
            raise IOError("ERROR: source specified with --step_parameters (-p) option, \
                {0}, does not have data directory: {1}".format(src, local_src_dir))

        alias_ctr = 0
        if args.chronos not in SPECIAL_MODES:
            for alias in sorted(os.listdir(local_src_dir)):
                jobname = "-".join(["fetch", src, alias])
                jobname = jobname.replace(".", "-")
                jobdict = generic_dict(args, None)
                jobdict.update({'TMPJOB': jobname,
                                'TMPLAUNCH': r'"schedule": "R1\/2200-01-01T06:00:00Z\/P3M"'
                               })
                ju.run_job_step(args, "placeholder", jobdict)

        for alias in sorted(os.listdir(local_src_dir)):
            alias_path = os.path.join(src, alias)
            local_alias_dir = os.path.join(local_src_dir, alias)
            alias_ctr += 1
            print("\t".join([src, str(alias_ctr), alias]))

            ## check for dependencies
            parents = []
            if args.dependencies != "":
                parents = args.dependencies.split(",,")

            metadata_file = os.path.join(local_alias_dir, "file_metadata.json")
            if not os.path.isfile(metadata_file):
                raise IOError("ERROR: Missing {0}".format(metadata_file))

            version_dict = {}
            with open(metadata_file, 'r') as infile:
                version_dict = json.load(infile)
            dependencies = version_dict["dependencies"]
            ismap = version_dict["is_map"]
            fetch_needed = version_dict["fetch_needed"] or args.force_fetch
            if dependencies:
                for dep in dependencies:
                    parent_string = "-".join(["fetch", src, dep])
                    parents.extend([parent_string])

            launchstr = r'"schedule": "R1\/\/P3M"'
            if parents:
                launchstr = ju.chronos_parent_str(parents)

            jobname = "-".join(["fetch", src, alias])
            jobname = jobname.replace(".", "-")
            jobdict = generic_dict(args, None)
            jobdict.update({'TMPJOB': jobname,
                            'TMPLAUNCH': launchstr,
                            'TMPALIASPATH': alias_path
                           })
            step_job = ju.run_job_step(args, "fetcher", jobdict)

            if not ismap and fetch_needed:
                ns_parameters.extend([",".join([src, alias])])
            if not args.setup and not args.one_step and not ismap and \
                args.chronos not in SPECIAL_MODES and fetch_needed:

                ns_jobname = "-".join([jobname, "next_step"])
                ns_dict = generic_dict(args, step_job.jobname)
                ns_dict.update({'TMPJOB': ns_jobname,
                                'TMPNEXTSTEP': "TABLE",
                                'TMPSTART': ",".join([src, alias]),
                                'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                                     '-d', ns_jobname])
                               })
                ju.run_job_step(args, "next_step_caller", ns_dict)

    if not args.setup and not args.one_step and args.chronos in SPECIAL_MODES \
        and ns_parameters:
        ns_dict = generic_dict(args, step_job.jobname)
        ns_dict.update({'TMPJOB': "-".join(["fetch", "next_step"]),
                        'TMPNEXTSTEP': "TABLE",
                        'TMPSTART': ",,".join(ns_parameters),
                        'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                             '-d', "-".join(["fetch", "next_step"])])
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        ju.run_job_step(tmpargs, "next_step_caller", ns_dict)

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
    if args.step_parameters == "":
        raise ValueError("ERROR: 'source,alias' must be specified with --step_parameters (-p)")

    ns_parameters = []
    step_job = ju.Job("tabler", args)

    for pair in alias_list:
        src, alias = pair.split(",")

        alias_path = os.path.join(src, alias)
        local_chunk_dir = os.path.join(args.working_dir, args.data_path, alias_path, "chunks")
        if not os.path.exists(local_chunk_dir):
            raise IOError('ERROR: "source,alias" specified with --step_parameters '
                          '(-p) option, ' + pair + ' does not have chunk directory:'
                          + local_chunk_dir)

        chunk_ctr = 0
        for chunk_name in sorted(os.listdir(local_chunk_dir)):
            if "raw_line" not in chunk_name or "unique" in chunk_name:
                continue
            output_files = chunk_name.replace('.raw_line.', '.*.')
            chunk_ctr += 1
            print("\t".join([str(chunk_ctr), chunk_name]))

            jobname = "-".join(["table", chunk_name])
            jobname = jobname.replace(".", "-")
            jobname = jobname.replace(".txt", "")
            jobdict = generic_dict(args, None)
            jobdict.update({'TMPJOB': jobname,
                            'TMPALIASPATH': alias_path,
                            'TMPCHUNK': os.path.join("chunks", chunk_name),
                            'TMPFILES': os.path.join("chunks", output_files)
                           })
            step_job = ju.run_job_step(args, "tabler", jobdict)

            ns_parameters.extend([chunk_name.replace('.raw_line.', '.table.')])

            if not args.setup and not args.one_step and args.chronos not in SPECIAL_MODES:
                ns_jobname = "-".join([jobname, "next_step"])
                ns_dict = generic_dict(args, step_job.jobname)
                ns_dict.update({'TMPJOB': ns_jobname,
                                'TMPNEXTSTEP': "MAP",
                                'TMPSTART': chunk_name.replace('.raw_line.', '.table.'),
                                'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                                     '-d', ns_jobname])
                               })
                ju.run_job_step(args, "next_step_caller", ns_dict)

    if not args.setup and not args.one_step and args.chronos in SPECIAL_MODES and \
        ns_parameters:
        ns_dict = generic_dict(args, step_job.jobname)
        ns_dict.update({'TMPJOB': "-".join(["table", "next_step"]),
                        'TMPNEXTSTEP': "MAP",
                        'TMPSTART': ",,".join(ns_parameters),
                        'TMPOPTS': " ".join([args.config_opts, args.workflow_opts,
                                             '-d', "-".join(["table", "next_step"])])
                       })
        tmpargs = args
        tmpargs.chronos = "LOCAL"
        ju.run_job_step(tmpargs, "next_step_caller", ns_dict)

    return 0


def run_map(args):
    """Runs id conversion for a single .table. file on the cloud.

    This loops through args.parameters tablefiles, creates a job for each that
    calls conv_utilities main(), and runs job in args.chronos location.

    Args:
        args (Namespace): args as populated namespace from parse_args, must
            specify --step_parameters(-p) as ',,' separated list of
            'source.alias.table.chunk.txt' file names
    """
    tablefile_list = args.step_parameters.split(",,")
    if args.step_parameters == "":
        raise ValueError("ERROR: 'tablefile' must be specified with --step_parameters (-p)")
    ju.Job("mapper", args)

    ctr = 0
    for filestr in tablefile_list:

        tablefile = os.path.basename(filestr)
        output_files = tablefile.replace('.table.', '.*.')
        src = tablefile.split('.')[0]
        alias = tablefile.split('.table.')[0].replace(src+'.', '', 1)

        chunk_path = os.path.join(src, alias, "chunks")
        local_chunk_dir = os.path.join(args.working_dir, args.data_path, chunk_path)
        local_tablefile = os.path.join(local_chunk_dir, tablefile)
        if not os.path.exists(local_tablefile):
            raise IOError('ERROR: "tablefile" specified with --step_parameters (-p) '
                          'option, ' + filestr + ' does not exist: ' + local_tablefile)

        ctr += 1
        print("\t".join([str(ctr), tablefile]))

        jobname = "-".join(["map", tablefile])
        jobname = jobname.replace(".", "-")
        jobname = jobname.replace(".txt", "")
        jobdict = generic_dict(args, None)
        jobdict.update({'TMPJOB': jobname,
                        'TMPTABLEPATH': os.path.join(chunk_path, tablefile),
                        'TMPFILES': os.path.join(chunk_path, output_files)
                       })
        ju.run_job_step(args, "mapper", jobdict)

    return 0


def run_import(args):
    """Merges sorted files and runs import on output file on the cloud.

    This loops through args.step_parameters (see Args below), and creates a job
    for each that merges the already sorted and unique files found in the data
    path (if args.merge is True), then calls import_utilities main().

    Args:
        args (Namespace): args as populated namespace from parse_args,
            specify --step_parameters(-p) as ',,' separated list of files to
            import or the allowed possible SQL table names: node, node_meta,
            edge2line, status, or edge_meta. If not specified, by default it
            will try to import all tables.
    """
    importfile_list = args.step_parameters.split(",,")
    tables = ['node', 'node_meta', 'edge2line', 'status', 'edge_meta', 'edge', 'raw_line']
    if args.step_parameters == "":
        importfile_list = tables
    ju.Job("importer", args)

    ctr = 0
    for importfile in importfile_list:
        if importfile in tables:
            mergefile = 'unique.' + importfile + '.txt'
            output_files = mergefile
            filestr = importfile
        else:
            output_files = importfile
            filestr = os.path.basename(importfile)
            if not os.path.exists(importfile):
                raise IOError('ERROR: "importfile" specified with --step_parameters (-p) '
                              'option, ' + importfile + ' does not exist: ' + importfile)
        ctr += 1
        print("\t".join([str(ctr), filestr]))

        jobname = "-".join(["import", filestr])
        jobname = jobname.replace(".", "-")
        jobname = jobname.replace(".txt", "")
        jobdict = generic_dict(args, None)
        base_dir = os.path.join(jobdict['TMPWORKDIR'], jobdict['TMPDATAPATH'])
        output_files.replace(base_dir, '')
        jobdict.update({'TMPJOB': jobname,
                        'TMPIMPORTPATH': importfile,
                        'TMPFILES': output_files
                       })
        ju.run_job_step(args, "importer", jobdict)

    return 0

def run_export(args):
    """
    TODO: Documentationr.

    Args:
        args (Namespace): args as populated namespace from parse_args,
            specify --step_parameters(-p) as ',,' separated list of files to
            import or the allowed possible SQL table names: node, node_meta,
            edge2line, status, or edge_meta. If not specified, by default it
            will try to import all tables.
    """
    export_list = args.step_parameters.split(",,")

    for num, expair in enumerate(export_list):
        print("\t".join([str(num), expair]))

        species, etype = expair.split('::')
        jobname = "-".join(["export", expair])
        jobname = jobname.replace(".", "-")
        jobname = jobname.replace("::", "--")
        jobdict = generic_dict(args, None)
        jobdict.update({'TMPJOB': jobname,
                        'TMPTAXON': species,
                        'TMPETYPE': etype,
                       })
        ju.run_job_step(args, "exporter", jobdict)

    return 0

def main():
    """Runs the 'start_step' step of the main or args.setup pipeline on the
    args.chronos location, and all subsequent steps if not args.one_step

    Parses the arguments and runs the specified part of the pipeline using the
    specified local or cloud resources.
    """

    args = main_parse_args()
    stage = 'PARSE'
    init_job = ''
    if args.dependencies == "":

        if args.setup:
            knownet = db.MySQL(None, args)
            knownet.init_knownet()
            stage = 'SETUP'
        elif args.start_step == 'IMPORT':
            stage = 'IMPORT'

        jobdict = generic_dict(args, None)
        jobdict['TMPJOB'] = "KN_starter_" + stage + args.time_stamp
        jobdict['TMPLAUNCH'] = r'"schedule": "R1\/2200-01-01T06:00:00Z\/P3M"'
        file_setup_job = ju.run_job_step(args, "file_setup", jobdict)
        args.dependencies = file_setup_job.jobname
        init_job = file_setup_job.jobname

    if args.setup:
        if args.start_step == 'CHECK':
            run_check(args)
        elif args.start_step == 'FETCH':
            run_fetch(args)
    else:
        if args.start_step == 'CHECK':
            run_check(args)
        elif args.start_step == 'FETCH':
            run_fetch(args)
        elif args.start_step == 'TABLE':
            run_table(args)
        elif args.start_step == 'MAP':
            run_map(args)
        elif args.start_step == 'IMPORT':
            run_import(args)
        elif args.start_step == 'EXPORT':
            run_export(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be ' +
                  str(POSSIBLE_STEPS))

    if init_job != '' and args.chronos not in SPECIAL_MODES:
        args.dependencies = ""
        jobdict = generic_dict(args, None)
        jobdict['TMPJOB'] = "KN_starter_" + stage + args.time_stamp
        file_setup_job = ju.run_job_step(args, "file_setup", jobdict)

if __name__ == "__main__":
    main()
