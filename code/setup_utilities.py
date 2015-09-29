"""Utiliites for running single or multiple steps of the supermaster pipeline
        either locally or on the cloud.

Classes:

Functions:
    run_local_check(args) -> : takes in all command line arguments.  Runs all
        necessary checks.  If args.run_mode is'PIPELINE', calls next step
    run_local_fetch(args) -> : takes in all command line arguments.  Runs all
        necessary fetches.  If args.run_mode is'PIPELINE', calls next step

    run_cloud_check(args) -> : takes in all command line arguments.  Runs all
        necessary checks on cloud.  If args.run_mode is'PIPELINE', each job
        calls its next step
    run_cloud_fetch(args) -> : takes in all command line arguments and a
        starting source (-p).  Runs all fetches for all aliases of specified
        source on cloud.  If args.run_mode is'PIPELINE', each job
        calls its next step

    curl_handler(args, jobname, job_str) -> : handles creating and sending
        jobs to the cloud
    list_parents(args, dependencies, response_str, parent_string) -> parents:
        given a list of dependencies, creates and tracks the parents required
        for the job sent to the cloud

Variables:
"""

from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as db
import os
import traceback
import sys
import re
import subprocess
import json

DEFAULT_START_STEP = 'CHECK'
DEFAULT_DEPLOY_LOC = 'LOCAL'
DEFAULT_RUN_MODE = 'STEP'
POSSIBLE_STEPS = ['CHECK', 'FETCH']
SETUP_FILES = ['species', 'ppi', 'ensembl']
CHECK_PY = "check_utilities"
FETCH_PY = "fetch_utilities"
IMPORT_PY = "import_utilities"
CURL_PREFIX = ["curl", "-i", "-L", "-H", "'Content-Type: application/json'",
               "-X", "POST"]
#HEADERS = {"Content-type": "application/json"}

def main_parse_args():
    """Processes command line arguments.

    Expects three positional arguments(start_step, deploy_loc, run_mode) and
    a number of optional arguments. If argument is missing, supplies default
    value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('start_step', help='select start step, must be CHECK, \
        FETCH ', default=DEFAULT_START_STEP)
    parser.add_argument('deploy_loc', help='select deployment type, must be \
        LOCAL or CLOUD ', default=DEFAULT_DEPLOY_LOC)
    parser.add_argument('run_mode', help='select run mode, must be STEP or \
        PIPELINE', default=DEFAULT_RUN_MODE)
    parser.add_argument('-p', '--step_parameters', help='parameters needed \
        for single call of step in pipeline', default='')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()

    config_opts = sys.argv[1:]
    config_opts.remove(args.start_step)
    config_opts.remove(args.deploy_loc)
    config_opts.remove(args.run_mode)
    if '-p' in config_opts:
        config_opts.remove('-p')
        config_opts.remove(args.step_parameters)
    args.config_opts = " ".join(config_opts)
    args.cloud_config_opts = cf.cloud_config_opts(args, config_opts)

    return args

def run_local_check(args):
    """Runs checks for all sources on local machine.

    This loops through all sources in the code directory and calls
    check_utilities clean() function on each source.

    Args:
        arguments from parse_args()

    Returns:
    """
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    checker = __import__(CHECK_PY)

    ctr = 0
    successful = 0
    failed = 0
    for module in SETUP_FILES:

        ctr += 1
        print(str(ctr) + "\t" + module)

        try:
            checker.check(module, args)
            successful += 1
        except Exception as err:
            print("ERROR: " + module + " could not be run")
            print("Message: " + str(err))
            print(traceback.format_exc())
            failed += 1

    print("CHECK FINISHED. Successful: {0}, Failed: {1}".format(successful, failed))
    if args.run_mode == "PIPELINE":
        run_local_fetch(args)

def run_local_fetch(args):
    """Runs fetches for all aliases on local machine.

    This loops through all aliases in the data directory and calls
    fetch_utilities main() function on each alias passing the
    file_metadata.json.

    Args:
        arguments from parse_args()

    Returns:
    """

    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    fetcher = __import__(FETCH_PY)
    #importer = __import__(IMPORT_PY)
    local_data_dir = os.path.join(args.local_dir, args.data_path)
    os.chdir(local_data_dir)
    ctr = 0
    successful = 0
    failed = 0
    for src_name in SETUP_FILES:
        print(src_name)
        for alias_name in sorted(os.listdir(os.path.join(local_data_dir, src_name))):
            alias_dir = os.path.join(local_data_dir, src_name, alias_name)
            if not os.path.isfile(os.path.join(alias_dir, "file_metadata.json")):
                continue

            os.chdir(alias_dir)
            ctr += 1
            print(str(ctr) + "\t" + alias_name)

            try:
                fetcher.main("file_metadata.json", args)
                #if src_name == 'ensembl':
                #    importer.db_import("file_metadata.json", args)
                successful += 1
            except Exception as err:
                print("ERROR: " + alias_name + " could not be fetched")
                print("Message: " + str(err))
                print(traceback.format_exc())
                failed += 1

    print("FETCH FINISHED. Successful: {0}, Failed: {1}".format(successful, failed))
    if args.run_mode == "PIPELINE":
        pass


def curl_handler(args, jobname, job_str):
    """handles creating and sending jobs to the cloud.

    Creates a json object in the code/chron_jobs directory using the job_str.
    Curls the json object to chronos specified in the input arguments.

    Args:
        args: arguments from parse_args()
        jobname: name for job on queue
        job_str: string description of json to submit to run job

    Returns:
    """
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    jobs_dir = os.path.join(local_code_dir, "chron_jobs")
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
    jobfile = jobs_dir + os.sep + jobname + ".json"

    with open(jobfile, 'w') as outfile:
        outfile.write(job_str)

    curl_cmd = list(CURL_PREFIX)
    curl_cmd.extend(["-d@" + jobfile])
    curl_cmd.extend([args.chronos + "/scheduler/iso8601"])
    print(" ".join(curl_cmd))
    #json.dumps(job_str)
    #connection.request("POST", "/scheduler/iso8601", "-d@"+jobfile, HEADERS)
    #connection.request("POST", "/scheduler/iso8601", json.dumps(job_str), HEADERS)
    #connection.getresponse().read()
    #subprocess.call(curl_cmd) #does not work

    #annoying workaround
    shfile = jobs_dir + os.sep + jobname + ".sh"
    with open(shfile, 'w') as outfile:
        outfile.write(" ".join(curl_cmd))
    os.chmod(shfile, 777)
    subprocess.call(['sh', "-c", shfile])
    os.remove(shfile)
    #connection.close()

def list_parents(args, dependencies, response_str, parent_string):
    """given a list of dependencies, creates and tracks the parents required
    for the job sent to the cloud

    For each dependency, checks if that parent is on the queue, if not, curls
    dummy job and adds to parent list.  If so, checks to see that the parent's
    last update was not a success and adds to parent list.  Returns list of
    parents to be added to json job description.

    Args:
        args: arguments from parse_args()
        dependencies: list of jobs dependencies
        response_str: array of json job descriptions on queue
        parent_string: string to map dependencies to parent job names

    Returns:
        parents: list of parents to be added to json job description.
    """
    parents = []
    jobs = json.loads(response_str)
    for depend in dependencies:
        dep_jobname = "-".join([parent_string, depend])
        jname = -1
        jsucc = -1
        jerr = -1
        for job in jobs:
            if dep_jobname == job["name"]:
                jname = job["name"]
                if job["lastSuccess"] is not '':
                    jsucc = job["lastSuccess"]
                if job["lastError"] is not '':
                    jerr = job["lastError"]
        # end loop through jobs
        print("\t".join([dep_jobname, str(jname), str(jsucc), str(jerr)]))
        if jname == -1: # no parent on queue
            # schedule dummy parent add dependancy
            dummy_str = ""
            with open(os.path.join(args.local_dir, args.code_path, 'template',
                                   "dummy_template.json"), 'r') as infile:
                dummy_str = infile.read(10000)

            dummy_str = cf.cloud_template_subs(args, dummy_str)
            dummy_str = dummy_str.replace("TMPJOB", dep_jobname)
            curl_handler(args, dep_jobname, dummy_str)
            parents.append(dep_jobname)

        elif jsucc == -1: # parent on queue but not succeeded
            # add dependency
            parents.append(dep_jobname)
        elif not jerr == -1: # parent on queue, succeed, has error
            if jsucc > jerr: # error happened before success
                # add dependency
                parents.append(dep_jobname)
    # end dependencies loop
    return parents


def run_cloud_check(args):
    """Runs checks for all sources on the cloud.

    This loops through all sources in the code directory, creates a
    json chronos jobs for each source that calls check_utilities
    clean() (and if run_mode 'PIPELINE', the call to
    setup_utilities FETCH) and curls json to chronos.

    Args:
        args: arguments from parse_args()

    Returns:
    """
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    template_file = os.path.join("template", "check_template.json")

    ctr = 0
    #connection = http.client.HTTPConnection(args.chronos)
    for module in SETUP_FILES:
        jobname = "-".join(["check", module])
        jobname = jobname.replace(".", "-")
        pipeline_cmd = ""
        if args.run_mode == "PIPELINE":
            arg_str = " ".join([args.deploy_loc, args.run_mode, args.cloud_config_opts])
            pipeline_cmd = "python3 /{0}/setup_utilities.py FETCH {1} -p {2}\
                            ;".format(args.code_path, arg_str, module)
        ctr += 1
        print(str(ctr) + "\t" + module)

        job_str = ""
        with open(template_file, 'r') as infile:
            job_str = infile.read(10000)

        job_str = cf.cloud_template_subs(args, job_str)
        job_str = job_str.replace("TMPJOB", jobname)
        job_str = job_str.replace("TMPSRC", module)
        job_str = job_str.replace("TMPPIPECMD", pipeline_cmd)

        curl_handler(args, jobname, job_str)

def run_cloud_fetch(args):
    """Runs fetches for all aliases of a single source on
    the cloud.

    For a single source, this loops through all aliases in the data directory,
    creates a json chronos jobs for each alias that calls fetch_utilities
    main() (and if run_mode 'PIPELINE', the call to )
    and curls json to chronos.

    Args:
        args: arguments from parse_args(), must specific --step_paramters(-p) as
        single source

    Returns:
    """
    src = args.step_parameters
    if src is '':
        print("ERROR: 'source' must be specified with --step_parameters (-p)")
        return -1
    print("'source' specified with --step_parameters (-p): {0}".format(src))
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    template_file = os.path.join("template", "fetch_template.json")

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
        if src == 'ensembl':
            pipeline_cmd = "/usr/bin/time -v python3 /{0}/import_utilities.py \
                            file_metadata.json {1};".format(args.code_path,
                                                            args.cloud_config_opts)
        if args.run_mode == "PIPELINE":
            pass

        ctr += 1
        print("\t".join([str(ctr), src, alias]))

        job_str = ""
        with open(template_file, 'r') as infile:
            job_str = infile.read(10000)

        job_str = cf.cloud_template_subs(args, job_str)
        job_str = job_str.replace("TMPJOB", jobname)
        job_str = job_str.replace("TMPALIASPATH", alias_path)
        job_str = job_str.replace("TMPPIPECMD", pipeline_cmd)

        curl_handler(args, jobname, job_str)

def main():
    """Runs the 'start_step' step of the pipeline on the 'deploy_loc' local or
    cloud location, and all subsequent steps if PIPELINE 'run_mode'

    Parses the arguments and runs the specified part of the pipeline using the
    specified local or cloud resources.

    Args:

    Returns:
    """

    args = main_parse_args()
    if not args.run_mode == 'PIPELINE' and not args.run_mode == 'STEP':
        print(args.run_mode + ' is an unacceptable run_mode.  Must be STEP or PIPELINE')
        return

    local_data_dir = os.path.join(args.local_dir, args.data_path)
    if not os.path.exists(local_data_dir):
        os.makedirs(local_data_dir)

    knownet = db.MySQL(None, args)
    knownet.init_knownet()

    if args.deploy_loc == 'LOCAL':
        if args.start_step == 'CHECK':
            run_local_check(args)
        elif args.start_step == 'FETCH':
            run_local_fetch(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be \
                ' + str(POSSIBLE_STEPS))
            return

    elif args.deploy_loc == 'CLOUD':
        if args.start_step == 'CHECK':
            run_cloud_check(args)
        elif args.start_step == 'FETCH':
            run_cloud_fetch(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be \
                ' + str(POSSIBLE_STEPS))
            return

    else:
        print(args.deploy_loc + ' is an unacceptable deploy_loc.  Must be LOCAL or CLOUD')
        return

    return


if __name__ == "__main__":
    sys.argv[len(sys.argv)-1] = re.sub(r';$', '', sys.argv[len(sys.argv)-1])
    main()
