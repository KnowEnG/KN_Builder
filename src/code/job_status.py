from argparse import ArgumentParser
import http.client
import json
import time
import subprocess
import os
from datetime import datetime
import socket



def main_parse_args():
    """Processes command line arguments.

    Expects a number of pipeline specific and global optional arguments.
    If argument is missing, supplies default value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument("-p", "--species", nargs='+', required=True)
    parser.add_argument("-s", "--source", nargs='+', required=True)
    parser.add_argument("-b", "--build_name", default="2test-1801")
    args = parser.parse_args()
    return args


def get_status():
    """Prints information on chronos jobs.
    """
    connection = http.client.HTTPConnection(KNP_CHRONOS_URL)
    connection.request("GET", "/scheduler/jobs")
    response = connection.getresponse().read()
    response_str = response.decode("utf-8")
    try:
        jobs = json.loads(response_str)
    except ValueError:
        print(response_str)
        return get_status()

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
        print("\t".join(['name', 'last_succ', 'last_err', 'pending', 'succeeded',
                         'threw_error', 'recovered']))
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


def wait_for_port(port, host="localhost", interval=30):
    good = False
    while not good:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            good = True
        except socket.error:
            pass
        finally:
            s.close()
        time.sleep(interval)


def run_step(step, wait=True):
    args = []

    if step == 'MYSQL':
        args = ['python3', KNP_CODE_PATH+'/mysql_utilities.py']
    elif step == 'REDIS':
        args = ["python3", KNP_CODE_PATH+"/redis_utilities.py"]
    elif step == 'SETUP':
        args = ['python3', KNP_CODE_PATH+'/workflow_utilities.py', 'CHECK', '-su', '-es', KNP_ENS_SPECIES]
    elif step == 'CHECK':
        args = ['python3', KNP_CODE_PATH+'/workflow_utilities.py', 'CHECK', '-p', KNP_ENS_SOURCE]
    elif step == 'IMPORT':
        args = ['python3', KNP_CODE_PATH+'/workflow_utilities.py', 'IMPORT']
    elif step == 'EXPORT1':
        args = ['env', 'KNP_MYSQL_HOST='+KNP_MYSQL_HOST,
                'KNP_MYSQL_PORT='+KNP_MYSQL_PORT, 'KNP_MYSQL_PASS='+KNP_MYSQL_PASS,
                'KNP_MYSQL_USER='+KNP_MYSQL_USER, 'KNP_REDIS_HOST='+KNP_REDIS_HOST,
                'KNP_REDIS_PORT='+KNP_REDIS_PORT, 'KNP_WORKING_DIR='+KNP_WORKING_DIR,
                'KNP_CODE_DIR='+KNP_CODE_DIR, 'KNP_DATA_PATH='+KNP_DATA_PATH,
                'KNP_LOGS_PATH='+KNP_LOGS_PATH, 'KNP_CHRONOS_URL='+KNP_CHRONOS_URL,
                'KNP_STORAGE_DIR='+KNP_STORAGE_DIR, 'KNP_EXPORT_DIR='+KNP_EXPORT_DIR,
                'KNP_ENS_SPECIES='+KNP_ENS_SPECIES, KNP_CODE_DIR + 'export1.sh']
    elif step == 'EXPORT2':
        args = ['env', 'KNP_MYSQL_HOST='+KNP_MYSQL_HOST,
                'KNP_MYSQL_PORT='+KNP_MYSQL_PORT, 'KNP_MYSQL_PASS='+KNP_MYSQL_PASS,
                'KNP_MYSQL_USER='+KNP_MYSQL_USER, 'KNP_REDIS_HOST='+KNP_REDIS_HOST,
                'KNP_REDIS_PORT='+KNP_REDIS_PORT, 'KNP_WORKING_DIR='+KNP_WORKING_DIR,
                'KNP_DATA_PATH='+KNP_DATA_PATH, 'KNP_LOGS_PATH='+KNP_LOGS_PATH,
                'KNP_CHRONOS_URL='+KNP_CHRONOS_URL, 'KNP_STORAGE_DIR='+KNP_STORAGE_DIR,
                'KNP_EXPORT_DIR='+KNP_EXPORT_DIR, 'KNP_ENS_SPECIES='+KNP_ENS_SPECIES,
                KNP_CODE_DIR + 'export2.sh']
    else:
        ValueError("Invalid step:", step)

    subprocess.check_call(args, stderr=subprocess.STDOUT, stdout=open('/dev/null', 'w'))
    #TODO: Redirect to a file?  What file?

    if wait and not wait_for_success():
        raise Exception("A job failed.")


if __name__ == "__main__":
    args = main_parse_args()
    KNP_ENS_SPECIES = ',,'.join(args.species)
    KNP_ENS_SOURCE = ',,'.join(args.source)
    KNP_BUILD_NAME = args.build_name

    from config_utilities import \
    DEFAULT_CODE_PATH as KNP_CODE_PATH, \
    DEFAULT_WORKING_DIR as KNP_WORKING_DIR, \
    DEFAULT_DATA_PATH as KNP_DATA_PATH, \
    DEFAULT_LOGS_PATH as KNP_LOGS_PATH, \
    DEFAULT_CHRONOS_URL as KNP_CHRONOS_URL, \
    DEFAULT_MARATHON_URL as KNP_MARATHON_URL, \
    DEFAULT_MYSQL_PORT as KNP_MYSQL_PORT, \
    DEFAULT_MYSQL_PASS as KNP_MYSQL_PASS, \
    DEFAULT_MYSQL_USER as KNP_MYSQL_USER, \
    DEFAULT_MYSQL_CONF as KNP_MYSQL_CONF, \
    DEFAULT_MYSQL_URL as KNP_MYSQL_URL, \
    DEFAULT_MYSQL_DIR as KNP_MYSQL_DIR, \
    DEFAULT_MYSQL_MEM as KNP_MYSQL_MEM, \
    DEFAULT_MYSQL_CPU as KNP_MYSQL_CPU, \
    DEFAULT_REDIS_URL as KNP_REDIS_URL, \
    DEFAULT_REDIS_PORT as KNP_REDIS_PORT, \
    DEFAULT_REDIS_PASS as KNP_REDIS_PASS, \
    DEFAULT_REDIS_DIR as KNP_REDIS_DIR, \
    DEFAULT_REDIS_MEM as KNP_REDIS_MEM, \
    DEFAULT_REDIS_CPU as KNP_REDIS_CPU

    if get_status():
        main()
    else:
        run_step("MYSQL", False)
        run_step("REDIS", False)
        wait_for_port(int(KNP_REDIS_PORT), KNP_REDIS_URL)
        wait_for_port(int(KNP_MYSQL_PORT), KNP_MYSQL_URL)
        run_step('SETUP')
        run_step('CHECK')
        run_step('IMPORT')
        run_step('EXPORT1')
        run_step('EXPORT2')
