from argparse import ArgumentParser
import http.client
import json
import config_utilities as cf
import time
import subprocess
from datetime import datetime

def main_parse_args():
    """Processes command line arguments.

    Expects a number of pipeline specific and global optional arguments.
    If argument is missing, supplies default value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args


KNP_MYSQL_HOST = '127.0.0.1'
KNP_MYSQL_PORT = '3306'
KNP_MYSQL_PASS = 'KnowEnG'
KNP_MYSQL_USER = 'root'
KNP_REDIS_HOST = 'knowcluster02.dyndns.org'
KNP_REDIS_PORT = '6379'
KNP_REDIS_PASS = 'KnowEnG'
KNP_WORKING_DIR= "/mnt/backup/knowtest/KN-20rep-1706/"
KNP_DATA_PATH = 'data_20rep-1706'
KNP_LOGS_PATH = 'logs_20rep-1706'
KNP_CHRONOS_URL = '127.0.0.1:8888'
KNP_STORAGE_DIR = KNP_WORKING_DIR
KNP_ENS_SPECIES = 'mus_musculus'
KNP_ENS_SOURCE = 'blast'


def get_status():
    """Prints information on chronos jobs.
    """
    connection = http.client.HTTPConnection(KNP_CHRONOS_URL)
    connection.request("GET", "/scheduler/jobs")
    response = connection.getresponse().read()
    response_str = response.decode("utf-8")
    jobs = json.loads(response_str)

    l = []
    for job in jobs:
        jname = -1
        jsucc = -1
        jerr = -1
        threw_error = 0
        recovered = 0
        pending = 0
        succeeded = 0
        jname = job["name"]
        if job["lastSuccess"] != '':
            jsucc = job["lastSuccess"]
            jsucc = datetime.strptime(jsucc, '%Y-%m-%dT%H:%M:%S.%fZ')
        if job["lastError"] != '':
            jerr = job["lastError"]
            jerr = datetime.strptime(jerr, '%Y-%m-%dT%H:%M:%S.%fZ')
        if jsucc == -1 and jerr == -1:
            pending = 1
        if jsucc != -1:
            succeeded = 1
        if jerr != -1:
            threw_error = 1
        if jsucc != -1 and jerr != -1 and jsucc > jerr:
            recovered = 1
        l.append([jname, jsucc, jerr, pending, succeeded, threw_error, recovered])

    return l


def is_running(jobs):
    return any(j[3] for j in jobs)


def is_succeeded(jobs):
    return all(j[4] for j in jobs)


def is_failed(jobs):
    return any(j[5] for j in jobs)


def main(full=True, end=None):
    jobs = get_status()
    if full:
        print("\t".join(['name', 'last_succ', 'last_err', 'pending', 'succeeded', 'threw_error', 'recovered']))
        for job in jobs:
            if job[5]:
                print("\t".join(map(str, job)))

    print(is_running(jobs), is_succeeded(jobs), is_failed(jobs), end=end)


def wait_for_success(interval=30):
    #TODO: fail if not jobs running for consecutive intevals
    while True:
        main(False, '\r')
        jobs = get_status()
        if is_succeeded(jobs):
            return True
        elif is_failed(jobs):
            return False
        time.sleep(interval)


def run_step_and_wait(step):
    args = []

    if step == 'SETUP':
        args = ['python3', 'code/workflow_utilities.py', 'CHECK', '-su', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR, '-es', KNP_ENS_SPECIES]
    elif step == 'CHECK':
        args = ['python3', 'code/workflow_utilities.py', 'CHECK', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR, '-p', KNP_ENS_SOURCE]
    elif step == 'IMPORT':
        args = ['python3', 'code/workflow_utilities.py', 'IMPORT', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR]
    elif step == 'EXPORT':
        args = ['env', 'KNP_MYSQL_HOST='+KNP_MYSQL_HOST, 'KNP_MYSQL_PORT='+KNP_MYSQL_PORT, 'KNP_MYSQL_PASS='+KNP_MYSQL_PASS, 'KNP_MYSQL_USER='+KNP_MYSQL_USER, 'KNP_REDIS_HOST='+KNP_REDIS_HOST, 'KNP_REDIS_PORT='+KNP_REDIS_PORT, 'KNP_WORKING_DIR='+KNP_WORKING_DIR, 'KNP_DATA_PATH='+KNP_DATA_PATH, 'KNP_LOGS_PATH='+KNP_LOGS_PATH, 'KNP_CHRONOS_URL='+KNP_CHRONOS_URL, 'KNP_STORAGE_DIR='+KNP_STORAGE_DIR]
    else:
        ValueError("Invalid step:", step)

    try:
        #subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise
    if not wait_for_success():
        raise Exception("A job failed.")


if __name__ == "__main__":
    if get_status():
        main()
    else:
        run_step_and_wait('SETUP')
        run_step_and_wait('CHECK')
        run_step_and_wait('IMPORT')
        run_step_and_wait('EXPORT')
