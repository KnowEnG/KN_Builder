"""module for running the kn_build pipeline.

Contains utilities for running pipeline steps and checking their statuses.

Contains module functions::

    main_parse_args()
    get_status(chronos_url, statuses=False)
    wait_for_success(chronos_url, interval=30)
    wait_for_port(port, host="localhost", interval=30)
    run_step(step, wait=True, args=cf.config_args())

Examples:
    To run with locally on human for all sources::

        $ python3 code/build_status.py

    To view all optional arguments that can be specified::

        $ python3 code/build_status.py -h

"""

import http.client
import json
import time
import csv
import subprocess
import os
import sys
import socket
from argparse import ArgumentParser
from io import StringIO
import config_utilities as cf


def main_parse_args():
    """Processes command line arguments.

    Expects a number of pipeline specific and global optional arguments.
    If argument is missing, supplies default value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    config_opts = sys.argv[1:]
    # add working_dir to config_opts
    found_wd = False
    for opt in ['-wd', '--working_dir']:
        if opt in config_opts:
            found_wd = True
    if not found_wd:
        config_opts.extend(['-wd', args.working_dir])
    args.config_opts = " ".join(config_opts)
    return args


def get_status(chronos_url, statuses=False):
    """Returns dict with running, failure, and fresh jobs and prints status details.
    """
    if statuses:
        print('Jobs on ' + chronos_url)
    connection = http.client.HTTPConnection(chronos_url)
    connection.request("GET", "/scheduler/jobs")
    response_str = connection.getresponse().read().decode("utf-8")
    jobs_dict = json.loads(response_str)

    connection.request("GET", "/scheduler/graph/csv")
    response_str = connection.getresponse().read().decode("utf-8")
    reader = csv.reader(StringIO(response_str), delimiter=',')
    jobs_csv = {}
    for row in reader:
        if row[0] == 'link':
            continue
        jobs_csv[row[1]] = row

    job_status = {}
    job_status['running'] = []
    job_status['failure'] = []
    job_status['fresh'] = []
    job_status['all'] = []
    for job in jobs_dict:
        jname = job['name']
        nerror = job['errorCount']
        nsuccess = job['successCount']
        #command = job['command']
        if statuses:
            print('\t'.join([jobs_csv[jname][2], jobs_csv[jname][3], str(nerror),
                             str(nsuccess), jname]))
        job_status['all'] = job_status['all'] + [jname]
        if jobs_csv[jname][3] == 'running':
            job_status['running'] = job_status['running'] + [jname]
        elif jobs_csv[jname][2] == 'failure':
            job_status['failure'] = job_status['failure'] + [jname]
        elif jobs_csv[jname][2] == 'fresh':
            job_status['fresh'] = job_status['fresh'] + [jname]
    return job_status


def wait_for_success(chronos_url, interval=30):
    """When nothing is running, return True is all jobs success and False otherwise"""
    last_chance = 0
    print('Waiting for jobs...')
    while True:
        time.sleep(interval)
        job_status = get_status(chronos_url)
        print_str = time.strftime("%H:%M:%S")
        all_str = " - all: " + ', '.join(sorted(job_status['all']))
        fresh_str = " - fresh: " + ', '.join(sorted(job_status['fresh']))
        fail_str = " - failures: " + ', '.join(sorted(job_status['failure']))
        run_str = " - running: " + ', '.join(sorted(job_status['running']))
        print(print_str + fail_str + run_str)
        # no running, failure, or pending jobs, head to next step
        if (len(job_status['running']) == 0 and len(job_status['fresh']) == 0 and
                len(job_status['failure']) == 0):
            print('Ready for the next Phase!')
            return True
        elif len(job_status['running']) == 0:
            # no running jobs, but some pending, give one last chance
            if len(job_status['fresh']) > 0 and last_chance < 2:
                print('No jobs running, but not all finished, checking...')
                last_chance = last_chance + 1
                continue
            if len(job_status['fresh']) > 0 and last_chance > 2:
                print('Fail: Some jobs are stuck!')
                return False
            if len(job_status['failure']) > 0:
                print('Fail: Some jobs have failed!')
                return False
        # there are jobs still running
        else:
            last_chance = 0



def wait_for_port(port, host="localhost", interval=30):
    """ function to wait for interval seconds until db connection available"""
    print('Waiting for database connections to be available...')
    good = False
    while not good:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            good = True
        except socket.error:
            pass
        finally:
            sock.close()
        time.sleep(interval)


def run_step(step, wait=True, args=cf.config_args()):
    """starts next phase of the kn_build and may wait until finished"""
    arg_list = []
    if step == 'MYSQL':
        arg_list = ['python3', os.path.join(args.code_path, 'mysql_utilities.py'),
                    args.config_opts]
    elif step == 'REDIS':
        arg_list = ["python3", os.path.join(args.code_path, 'redis_utilities.py'),
                    args.config_opts]
    elif step == 'SETUP':
        arg_list = ['python3', os.path.join(args.code_path, 'workflow_utilities.py'),
                    'CHECK', '-su', args.config_opts]
    elif step == 'CHECK':
        arg_list = ['python3', os.path.join(args.code_path, 'workflow_utilities.py'),
                    'CHECK', '-p', args.src_classes, args.config_opts]
    elif step == 'IMPORT':
        arg_list = ['python3', os.path.join(args.code_path, 'workflow_utilities.py'),
                    'IMPORT', args.config_opts]
    elif step == 'EXPORT1':
        # TODO: change these to make use of the python
        arg_list = ['env', 'KNP_EXPORT_PATH='+args.export_path, 'KNP_CODE_DIR='+args.code_path,
                    'KNP_WORKING_DIR='+args.working_dir, 'KNP_DATA_PATH='+args.data_path,
                    'KNP_MYSQL_HOST='+args.mysql_host, 'KNP_MYSQL_PORT='+args.mysql_port,
                    'KNP_MYSQL_PASS='+args.mysql_pass, 'KNP_MYSQL_USER='+args.mysql_user,
                    'KNP_REDIS_HOST='+args.redis_host, 'KNP_REDIS_PORT='+args.redis_port,
                    'KNP_CONFIG_OPTS="'+args.config_opts+'"',
                    os.path.join(args.code_path, 'export1.sh')]
    elif step == 'EXPORT2':
        arg_list = ['env', 'KNP_EXPORT_DIR='+os.path.join(args.working_dir, args.export_path),
                    os.path.join(args.code_path, 'export2.sh')]
    else:
        ValueError("Invalid step:", step)

    log_file = os.path.join(args.working_dir, args.logs_path, step) + '.log'
    subprocess.check_call(" ".join(arg_list), shell=True, stderr=subprocess.STDOUT,
                          stdout=open(log_file, 'w'))

    if wait and not wait_for_success(args.chronos, 30):
        raise Exception("A job failed.")


def main():
    """controls sequence of build pipeline"""
    args = main_parse_args()

    log_dir = os.path.join(args.working_dir, args.logs_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # if there are scheduled jobs, return
    job_status = get_status(args.chronos)
    if len(job_status['all']) > 0:
        print("Cannot begin build with pre-existing jobs on chronos!")
    else:
        #run_step("MYSQL", False, args)
        #run_step("REDIS", False, args)
        #wait_for_port(int(args.redis_port), args.redis_host)
        #wait_for_port(int(args.mysql_port), args.mysql_host)
        #run_step('SETUP', True, args)
        #run_step('CHECK', True, args)
        #run_step('IMPORT', True, args)
        run_step('EXPORT1', True, args)
        run_step('EXPORT2', True, args)
        print("KnowNet Pipeline Completed!")

if __name__ == "__main__":
    main()
