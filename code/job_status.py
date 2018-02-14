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
        args = ['python3', 'code/mysql_utilities.py', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER,  '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-sd', KNP_STORAGE_DIR, "-mym", KNP_MYSQL_MEM, "-myc", KNP_MYSQL_CPU, "-myd", KNP_MYSQL_DIR, "-mycf", KNP_MYSQL_CONF, "-m", KNP_MARATHON_URL]
    elif step == 'REDIS':
        args = ["python3", "code/redis_utilities.py", "-rh", KNP_REDIS_HOST, "-rp", KNP_REDIS_PORT, "-rm", KNP_REDIS_MEM, "-rc", KNP_REDIS_CPU, "-rd", KNP_REDIS_DIR, "-rps", KNP_REDIS_PASS, "-m", KNP_MARATHON_URL, "-wd", KNP_WORKING_DIR, "-lp", KNP_LOGS_PATH]
    elif step == 'SETUP':
        args = ['python3', 'code/workflow_utilities.py', 'CHECK', '-su', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR, '-es', KNP_ENS_SPECIES]
    elif step == 'CHECK':
        args = ['python3', 'code/workflow_utilities.py', 'CHECK', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR, '-p', KNP_ENS_SOURCE]
    elif step == 'IMPORT':
        args = ['python3', 'code/workflow_utilities.py', 'IMPORT', '-myh', KNP_MYSQL_HOST, '-myp', KNP_MYSQL_PORT, '-myps', KNP_MYSQL_PASS, '-myu', KNP_MYSQL_USER, '-rh', KNP_REDIS_HOST, '-rp', KNP_REDIS_PORT, '-wd', KNP_WORKING_DIR, '-dp', KNP_DATA_PATH, '-lp', KNP_LOGS_PATH, '-c', KNP_CHRONOS_URL, '-sd', KNP_STORAGE_DIR]
    elif step == 'EXPORT1':
        args = ['env', 'KNP_MYSQL_HOST='+KNP_MYSQL_HOST, 'KNP_MYSQL_PORT='+KNP_MYSQL_PORT, 'KNP_MYSQL_PASS='+KNP_MYSQL_PASS, 'KNP_MYSQL_USER='+KNP_MYSQL_USER, 'KNP_REDIS_HOST='+KNP_REDIS_HOST, 'KNP_REDIS_PORT='+KNP_REDIS_PORT, 'KNP_WORKING_DIR='+KNP_WORKING_DIR, 'KNP_DATA_PATH='+KNP_DATA_PATH, 'KNP_LOGS_PATH='+KNP_LOGS_PATH, 'KNP_CHRONOS_URL='+KNP_CHRONOS_URL, 'KNP_STORAGE_DIR='+KNP_STORAGE_DIR, 'KNP_EXPORT_DIR='+KNP_EXPORT_DIR, 'KNP_ENS_SPECIES='+KNP_ENS_SPECIES, 'code/export1.sh']
    elif step == 'EXPORT2':
        args = ['env', 'KNP_MYSQL_HOST='+KNP_MYSQL_HOST, 'KNP_MYSQL_PORT='+KNP_MYSQL_PORT, 'KNP_MYSQL_PASS='+KNP_MYSQL_PASS, 'KNP_MYSQL_USER='+KNP_MYSQL_USER, 'KNP_REDIS_HOST='+KNP_REDIS_HOST, 'KNP_REDIS_PORT='+KNP_REDIS_PORT, 'KNP_WORKING_DIR='+KNP_WORKING_DIR, 'KNP_DATA_PATH='+KNP_DATA_PATH, 'KNP_LOGS_PATH='+KNP_LOGS_PATH, 'KNP_CHRONOS_URL='+KNP_CHRONOS_URL, 'KNP_STORAGE_DIR='+KNP_STORAGE_DIR, 'KNP_EXPORT_DIR='+KNP_EXPORT_DIR, 'KNP_ENS_SPECIES='+KNP_ENS_SPECIES, 'code/export2.sh']
    else:
        ValueError("Invalid step:", step)

    subprocess.check_call(args, stderr=subprocess.STDOUT, stdout=open('/dev/null', 'w')) #TODO: Redirect to a file?  What file?
    if wait and not wait_for_success():
        raise Exception("A job failed.")


if __name__ == "__main__":
    args = main_parse_args()
    KNP_ENS_SPECIES = ',,'.join(args.species)
    KNP_ENS_SOURCE = ',,'.join(args.source)
    KNP_BUILD_NAME = args.build_name
    KNP_WORKING_DIR = os.path.abspath('..')
    KNP_STORAGE_DIR = KNP_WORKING_DIR
    KNP_DATA_PATH = "data-"+KNP_BUILD_NAME
    KNP_EXPORT_DIR = KNP_WORKING_DIR+"/userKN-"+KNP_BUILD_NAME
    KNP_LOGS_PATH = "logs-"+KNP_BUILD_NAME
    KNP_CHRONOS_URL = '127.0.0.1:8888'
    KNP_MARATHON_URL='127.0.0.1:8080/v2/apps'
    
    KNP_MYSQL_HOST = '127.0.0.1'
    KNP_MYSQL_PORT = '3306'
    KNP_MYSQL_PASS = 'KnowEnG'
    KNP_MYSQL_USER = 'root'
    KNP_MYSQL_CONF = 'build_conf/'
    KNP_MYSQL_DIR = KNP_WORKING_DIR+'/mysql-'+KNP_MYSQL_PORT+'-'+KNP_BUILD_NAME
    KNP_MYSQL_MEM = '0'
    KNP_MYSQL_CPU = '0.5'
    
    KNP_REDIS_HOST = '127.0.0.1'
    KNP_REDIS_PORT = '6380'
    KNP_REDIS_PASS = 'KnowEnG'
    KNP_REDIS_DIR = KNP_WORKING_DIR+'/redis-'+KNP_REDIS_PORT+'-'+KNP_BUILD_NAME
    KNP_REDIS_MEM = '0'
    KNP_REDIS_CPU = '0.5'

    #if get_status():
    #    main()
    #else:
    run_step("MYSQL", False)
    run_step("REDIS", False)
    wait_for_port(int(KNP_REDIS_PORT), KNP_REDIS_HOST)
    wait_for_port(int(KNP_MYSQL_PORT), KNP_MYSQL_HOST)
    #    run_step('SETUP')
    #    run_step('CHECK')
    #    run_step('IMPORT')
    run_step('EXPORT1')
    run_step('EXPORT2')
