"""Utiliites for running single or multiple steps of the pipeline either
        locally or on the cloud.

Classes:

Functions:
    run_local_check(args) -> : takes in all command line arguments.  Runs all 
        necessary checks.  If args.run_mode is'PIPELINE', calls next step
    run_local_fetch(args) -> : takes in all command line arguments.  Runs all 
        necessary fetches.  If args.run_mode is'PIPELINE', calls next step
    run_local_table(args) -> : takes in all command line arguments.  Runs all 
        necessary tables.  If args.run_mode is'PIPELINE', calls next step

    run_cloud_check(args) -> : takes in all command line arguments.  Runs all 
        necessary checks on cloud.  If args.run_mode is'PIPELINE', each job 
        calls its next step
        

Variables:
"""

from argparse import ArgumentParser
import config_utilities as cf
import os
import re
import traceback
import sys
import subprocess
import json
import http.client

DEFAULT_START_STEP = 'CHECK'
DEFAULT_DEPLOY_LOC = 'LOCAL'
DEFAULT_RUN_MODE = 'STEP'
POSSIBLE_STEPS = ['CHECK', 'FETCH', 'TABLE']
CHECK_PY = "check_utilities"
FETCH_PY = "fetch_utilities"
TABLE_PY = "table_utilities"
CURL_PREFIX = ["curl", "-i", "-L", "-H", "'Content-Type: application/json'", "-X", "POST"]
headers = {"Content-type": "application/json"}

def parse_args():
    """Processes command line arguments.

    Expects three positional arguments(start_step, deploy_loc, run_mode) and 
    a number of optional arguments. If argument is missing, supplies default 
    value.
    
    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('start_step', help='select start step, must be CHECK, FETCH, or TABLE ', default=DEFAULT_START_STEP)
    parser.add_argument('deploy_loc', help='select deployment type, must be LOCAL or CLOUD ', default=DEFAULT_DEPLOY_LOC)
    parser.add_argument('run_mode', help='select run mode, must be STEP or PIPELINE', default=DEFAULT_RUN_MODE)
    parser.add_argument('-i', '--image', help='docker image name for pipeline', default=cf.DEFAULT_DOCKER_IMG)
    parser.add_argument('-c', '--chronos', help='url of chronos scheduler', default=cf.DEFAULT_CURL_URL)
    parser.add_argument('-ld', '--local_dir', help='name of toplevel directory on local machine', default=cf.DEFAULT_LOCAL_BASE)
    parser.add_argument('-cd', '--cloud_dir', help='name of toplevel directory on cloud storage', default=cf.DEFAULT_CLOUD_BASE)
    parser.add_argument('-cp', '--code_path', help='relative path of code directory from toplevel ', default=cf.DEFAULT_CODE_PATH)
    parser.add_argument('-dp', '--data_path', help='relative path of data directory from toplevel', default=cf.DEFAULT_DATA_PATH)
    parser.add_argument('-p', '--step_parameters', help='parameters needed for single call of step in pipeline', default='')
    args = parser.parse_args()
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
    for filename in sorted(os.listdir(local_code_dir)):
        if not filename.endswith(".py"): continue
        if 'utilities' in filename: continue

        ctr += 1;
        module = os.path.splitext(filename)[0]
        print(str(ctr) + "\t" + module)

        try:
            checker.check(module)
            successful += 1
        except Exception as e:
            print ("ERROR: " + module + " could not be run")
            print ("Message: " + str(e))
            print (traceback.format_exc())
            failed += 1

    print ("CHECK FINISHED. Successful: {0}, Failed: {1}".format(successful, failed))
    if(args.run_mode == "PIPELINE"):
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
    local_data_dir = os.path.join(args.local_dir, args.data_path)
    os.chdir(local_data_dir)
    ctr = 0
    successful = 0
    failed = 0
    for src_name in sorted(os.listdir(local_data_dir)):
        print(src_name)
        for alias_name in sorted(os.listdir(os.path.join(local_data_dir, src_name))):
            alias_dir = os.path.join(local_data_dir, src_name, alias_name)
            if not os.path.isfile(os.path.join(alias_dir, "file_metadata.json")):
                continue

            os.chdir(alias_dir)
            ctr += 1;
            print(str(ctr) + "\t" + alias_name)

            try:
                fetcher.main("file_metadata.json")
                successful += 1
            except Exception as e:
                print ("ERROR: " + alias_name + " could not be fetched")
                print ("Message: " + str(e))
                print (traceback.format_exc())
                failed += 1

    print ("FETCH FINISHED. Successful: {0}, Failed: {1}".format(successful, failed))
    if(args.run_mode == "PIPELINE"):
        run_local_table(args)

def run_local_table(args):
    """Runs tables for all aliases on local machine.

    This loops through all chunks in the data directory and calls
    table_utilities main() function on each chunk passing the name of the
    chunk and the file_metadata.json.

    Args:
        arguments from parse_args()

    Returns:
    """

    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    tabler = __import__(TABLE_PY)
    local_data_dir = os.path.join(args.local_dir, args.data_path)
    os.chdir(local_data_dir)
    ctr = 0
    successful = 0
    failed = 0
    for src_name in sorted(os.listdir(local_data_dir)):
        print(src_name)
        for alias_name in sorted(os.listdir(os.path.join(local_data_dir, src_name))):
            print("\t" + alias_name)
            alias_dir = os.path.join(local_data_dir, src_name, alias_name)
            if not os.path.isfile(os.path.join(alias_dir, "file_metadata.json")):
                continue
            chunkdir = os.path.join(alias_dir, "chunks")
            if not os.path.exists(chunkdir):
                continue

            os.chdir(alias_dir)
            for chunk_name in sorted(os.listdir(chunkdir)):
                if "rawline" not in chunk_name:
                    continue

                chunkfile = os.path.join("chunks", chunk_name)
                ctr += 1;
                print(str(ctr) + "\t\t" + chunk_name)

                try:
                    tabler.main(chunkfile, "file_metadata.json")
                    successful += 1
                except Exception as e:
                    print ("ERROR: " + chunk_name + " could not be tabled")
                    print ("Message: " + str(e))
                    print (traceback.format_exc())
                    failed += 1

    print ("TABLE FINISHED. Successful: {0}, Failed: {1}".format(successful, failed))
    if(args.run_mode == "PIPELINE"):
        pass


def run_cloud_check(args):
    """Runs checks for all sources on the cloud.

    This loops through all sources in the code directory, creates a 
    json chronos jobs for each source that calls check_utilities
    clean() (and if run_mode 'PIPELINE', the call to 
    pipeline_utilities FETCH) and curls json to chronos.

    Args:
        arguments from parse_args()

    Returns:
    """
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    jobs_dir = os.path.join(local_code_dir, "chron_jobs")
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
    template_file = "check_template.json"

    cloud_code_dir = os.path.join(args.cloud_dir, args.code_path)
    cloud_data_dir = os.path.join(args.cloud_dir, args.data_path)

    ctr = 0
#    connection = http.client.HTTPConnection(args.chronos)
    for filename in sorted(os.listdir(local_code_dir)):
        if not filename.endswith(".py"): continue
        if 'utilities' in filename: continue

        module = os.path.splitext(filename)[0]
        jobname = "-".join(["check",module])
        jobname = jobname.replace(".","-")
        jobfile = jobs_dir + os.sep + jobname + ".json"
        pipeline_cmd = ""
        if(args.run_mode == "PIPELINE"):
            new_opts = [opt.replace(args.local_dir, '/') for opt in sys.argv[2:]]
            pipeline_cmd = "python3 /code/pipeline_utilities.py FETCH {0} -p {1} 2> /code/fetch-{2}.err;".format(" ".join(new_opts), module, module)
        ctr += 1;
        print(str(ctr) + "\t" + module)

        with open(template_file, 'r') as infile:
            job_str = infile.read(10000)
            job_str = job_str.replace("TMPJOB", jobname)
            job_str = job_str.replace("TMPIMG", args.image)
            job_str = job_str.replace("TMPDATADIR", cloud_data_dir)
            job_str = job_str.replace("TMPCODEDIR", cloud_code_dir)
            job_str = job_str.replace("TMPSRC", module)
            job_str = job_str.replace("TMPPIPECMD", pipeline_cmd)

        with open(jobfile, 'w') as outfile:
            outfile.write(job_str)

        curl_cmd = list(CURL_PREFIX)
        curl_cmd.extend(["-d@" + jobfile])
        curl_cmd.extend([args.chronos + "/scheduler/iso8601"])
        print(" ".join(curl_cmd))
        #json.dumps(job_str)
        #connection.request("POST", "/scheduler/iso8601", "-d@"+jobfile, headers)
        #connection.request("POST", "/scheduler/iso8601", json.dumps(job_str), headers)
        #connection.getresponse().read()
        #subprocess.call(curl_cmd) #does not work

        #annoying workaround
        shfile = jobs_dir + os.sep + jobname + ".sh"
        with open(shfile, 'w') as outfile:
            outfile.write(" ".join(curl_cmd))
        os.chmod(shfile, 777)    
        subprocess.call(['sh', "-c", shfile])
        os.remove(shfile)
#    connection.close()


def run_cloud_fetch(args):
    """Runs fetches for all aliases of a single source on 
    the cloud.

    For a single source, this loops through all aliases in the data directory, 
    creates a json chronos jobs for each alias that calls fetch_utilities
    main() (and if run_mode 'PIPELINE', the call to pipeline_utilities TABLE) 
    and curls json to chronos.

    Args:
        arguments from parse_args(), must specific --step_paramters(-p) as 
        single source

    Returns:
    """
    src = args.step_parameters
    if(src is ''):
        print("ERROR: 'source' must be specified with --step_parameters (-p)")   
        return -1
    print("'source' specified with --step_parameters (-p): {0}".format(src))
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    jobs_dir = os.path.join(local_code_dir, "chron_jobs")
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
    template_file = "fetch_template.json"

    cloud_code_dir = os.path.join(args.cloud_dir, args.code_path)
    cloud_data_dir = os.path.join(args.cloud_dir, args.data_path)

    local_src_dir = os.path.join(args.local_dir, args.data_path, src)
    if not os.path.exists(local_src_dir):
        print ("ERROR: source specified with --step_parameters (-p) option, {0},does not have data directory: {1}".format(src, local_src_dir))
        return -1

    ctr = 0
    for alias in sorted(os.listdir(local_src_dir)):

        alias_path = os.path.join(src,alias)
        jobname = "-".join(["fetch",src,alias])
        jobname = jobname.replace(".","-")
        jobfile = jobs_dir + os.sep + jobname + ".json"
        pipeline_cmd = ""
        print(args.run_mode)
        if(args.run_mode == "PIPELINE"):
            new_opts = [opt.replace(args.local_dir, '/') for opt in sys.argv[2:]]
            if '-p' in new_opts:
                new_opts.remove('-p')
                new_opts.remove(args.step_parameters)
            pipeline_cmd = "python3 /code/pipeline_utilities.py TABLE {0} -p {1} 2> /code/table-{2}.err;".format(" ".join(new_opts), src + "," + alias, src + "," + alias)
        ctr += 1;
        print("\t".join([str(ctr),src,alias]))

        with open(template_file, 'r') as infile:
            job_str = infile.read(10000)
            job_str = job_str.replace("TMPJOB", jobname)
            job_str = job_str.replace("TMPIMG", args.image)
            job_str = job_str.replace("TMPDATADIR", cloud_data_dir)
            job_str = job_str.replace("TMPCODEDIR", cloud_code_dir)
            job_str = job_str.replace("TMPALIASPATH", alias_path)
            job_str = job_str.replace("TMPPIPECMD", pipeline_cmd)

        with open(jobfile, 'w') as outfile:
            outfile.write(job_str)

        curl_cmd = list(CURL_PREFIX)
        curl_cmd.extend(["-d@" + jobfile])
        curl_cmd.extend([args.chronos + "/scheduler/iso8601"])
        print(" ".join(curl_cmd))
        #subprocess.call(curl_cmd) #does not work

        #annoying workaround
        shfile = jobs_dir + os.sep + jobname + ".sh"
        with open(shfile, 'w') as outfile:
            outfile.write(" ".join(curl_cmd))
        os.chmod(shfile, 777)    
        subprocess.call(['sh', "-c", shfile])
        os.remove(shfile)
    

def run_cloud_table(args):
    """Runs table for a chunk from a single alias on the cloud.

    For a single alias, this loops through all chunks in its data directory, 
    creates a json chronos jobs for each alias that calls fetch_utilities
    main() (and if run_mode 'PIPELINE', the call to pipeline_utilities TABLE) 
    and curls json to chronos.

    Args:
        arguments from parse_args(), must specific --step_paramters(-p) as 
        single source

    Returns:
    """
    src, alias = args.step_parameters.split(",")
    if(args.step_parameters is ''):
        print("ERROR: 'source,alias' must be specified with --step_parameters (-p)")   
        return -1
    print("'source,alias' specified with --step_parameters (-p): {0}".format(args.step_parameters))
    
    local_code_dir = os.path.join(args.local_dir, args.code_path)
    os.chdir(local_code_dir)
    jobs_dir = os.path.join(local_code_dir, "chron_jobs")
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
    template_file = os.path.join(local_code_dir, "table_template.json")
    dummy_template_file = os.path.join(local_code_dir, "dummy_template.json")

    cloud_code_dir = os.path.join(args.cloud_dir, args.code_path)
    cloud_data_dir = os.path.join(args.cloud_dir, args.data_path)

    alias_path = os.path.join(src,alias)
    local_alias_dir = os.path.join(args.local_dir, args.data_path, alias_path)
    if not os.path.exists(local_alias_dir):
        print ("ERROR: 'source,alias' specified with --step_parameters (-p) option, {0}, does not have data directory: {1}".format(args.step_parameters, local_alias_dir))
        return -1
    
    if not os.path.isfile(os.path.join(local_alias_dir, "file_metadata.json")):
        print ("ERROR: cannot find file_metadata.json in {0}".format(local_alias_dir))
        return
            
    local_chunk_dir = os.path.join(local_alias_dir, "chunks")
    if not os.path.exists(local_chunk_dir):
        return

    os.chdir(local_alias_dir)
    ctr = 0

    connection = http.client.HTTPConnection(args.chronos)
    for chunk_name in sorted(os.listdir(local_chunk_dir)):
        if "rawline" not in chunk_name:
            continue

        chunkfile = os.path.join("chunks", chunk_name)
        ctr += 1;
        print(str(ctr) + "\t" + chunk_name)
    
        jobname = "-".join(["table", chunk_name])
        jobname = jobname.replace(".txt","")
        jobname = jobname.replace(".","-")
        
        jobfile = jobs_dir + os.sep + jobname + ".json"
        pipeline_cmd = ""
#        if(args.run_mode == "PIPELINE"):

        ctr += 1;
        print("\t".join([str(ctr),chunk_name]))

        with open(template_file, 'r') as infile:
            job_str = infile.read(10000)
            job_str = job_str.replace("TMPJOB", jobname)
            job_str = job_str.replace("TMPIMG", args.image)
            job_str = job_str.replace("TMPDATADIR", cloud_data_dir)
            job_str = job_str.replace("TMPCODEDIR", cloud_code_dir)
            job_str = job_str.replace("TMPALIASPATH", alias_path)
            job_str = job_str.replace("TMPCHUNK", chunkfile)
            job_str = job_str.replace("TMPPIPECMD", pipeline_cmd)

            ## check for dependencies
            with open("file_metadata.json", 'r') as infile:
                version_dict = json.load(infile)
                dependencies = version_dict["dependencies"]
                if len(dependencies) > 0:
                
                    parents = []
                
                    # check status of queue
                    connection.request("GET", "/scheduler/jobs")
                    response = connection.getresponse().read()
                    response_str = response.decode("utf-8") 
                
                    #annoying workaround
                    #getjson = jobs_dir + os.sep + jobname + ".get.json"
                    #get_curl = 'curl -L -X GET {0}/scheduler/jobs > {1}'.format(args.chronos, getjson)
                    #shfile = jobs_dir + os.sep + jobname + ".sh"
                    #with open(shfile, 'w') as outfile:
                    #    outfile.write(get_curl)
                    #os.chmod(shfile, 777)    
                    #subprocess.call(['sh', "-c", shfile])
                    #os.remove(shfile)
            
                    #with open(getjson, 'r') as infile2:
                    #    queue_dict = json.load(infile2)
                
                    jobs = json.loads(response_str)
                    for depend in dependencies:
                        dep_jobname = "-".join(["fetch", src, depend])
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
                        print ("\t".join([chunk_name, depend, dep_jobname, jname, str(jsucc), str(jerr)]))
                        if jname == -1: # no parent on queue
                            # schedule dummy parent add dependancy
                            with open(dummy_template_file, 'r') as infile:
                                dummy_str = infile.read(10000)
                                dummy_str = dummy_str.replace("TMPJOB", dep_jobname)
                                dummy_str = dummy_str.replace("TMPIMG", args.image)
                                dummy_str = dummy_str.replace("TMPDATADIR", cloud_data_dir)
                                dummy_str = dummy_str.replace("TMPCODEDIR", cloud_code_dir)
                                dummyfile = jobs_dir + os.sep + dep_jobname + ".json"
                                with open(dummyfile, 'w') as outfile:
                                    outfile.write(dummy_str)

                                curl_cmd = list(CURL_PREFIX)
                                curl_cmd.extend(["-d@" + dummyfile])
                                curl_cmd.extend([args.chronos + "/scheduler/iso8601"])
                                print(" ".join(curl_cmd))
                                #subprocess.call(curl_cmd) #does not work

                                #annoying workaround
                                shfile = jobs_dir + os.sep + jobname + ".sh"
                                with open(shfile, 'w') as outfile:
                                    outfile.write(" ".join(curl_cmd))
                                os.chmod(shfile, 777)    
                                subprocess.call(['sh', "-c", shfile])
                                os.remove(shfile)

                            parents.append(dep_jobname)
                        elif jsucc == -1: # parent on queue but not succeeded
                            # add dependency
                            parents.append(dep_jobname)
        
                        elif not jerr == -1: # parent on queue, succeed, has error
                            if jsucc > jerr: # error happened before success
                                # add dependency
                                parents.append(dep_jobname)
                    # end dependencies loop
                # end if dependencies
                #os.remove(getjson)
                launch_cmd = '"schedule": "R1\/\/P3M"'  
                print(parents)
                if len(parents) > 0:
                    launch_cmd = '"parents": ' + str(parents)
                job_str = job_str.replace("TMPLAUNCH", launch_cmd)
            
            # end open metadata
            with open(jobfile, 'w') as outfile:
                outfile.write(job_str)
        
        # end open template file
        curl_cmd = list(CURL_PREFIX)
        curl_cmd.extend(["-d@" + jobfile])
        curl_cmd.extend([args.chronos + "/scheduler/iso8601"])
        print(" ".join(curl_cmd))
        #subprocess.call(curl_cmd) #does not work

        #annoying workaround
        shfile = jobs_dir + os.sep + jobname + ".sh"
        with open(shfile, 'w') as outfile:
            outfile.write(" ".join(curl_cmd))
        os.chmod(shfile, 777)    
        subprocess.call(['sh', "-c", shfile])
        os.remove(shfile)
    # end chunk
    connection.close()


def main():
    """Runs the 'start_step' step of the pipeline on the 'deploy_loc' local or 
    cloud location, and all subsequent steps if PIPELINE 'run_mode'

    Parses the arguments and runs the specified part of the pipeline using the 
    specified local or cloud resources.

    Args:

    Returns:
    """

    args = parse_args()
    if not args.run_mode == 'PIPELINE' and not args.run_mode == 'STEP':
        print(args.run_mode + ' is an unacceptable run_mode.  Must be STEP or PIPELINE')
        return

    if args.deploy_loc == 'LOCAL':
        if args.start_step == 'CHECK':
            run_local_check(args)
        elif args.start_step == 'FETCH':
            run_local_fetch(args)
        elif args.start_step == 'TABLE':
            run_local_table(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be ' + str(POSSIBLE_STEPS))
            return

    elif args.deploy_loc == 'CLOUD':
        if args.start_step == 'CHECK':
            run_cloud_check(args)
        elif args.start_step == 'FETCH':
            run_cloud_fetch(args)
        elif args.start_step == 'TABLE':
            run_cloud_table(args)
        else:
            print(args.start_step + ' is an unacceptable start_step.  Must be ' + str(POSSIBLE_STEPS))
            return

    else:
        print(args.deploy_loc + ' is an unacceptable deploy_loc.  Must be LOCAL or CLOUD')
        return

    return


if __name__ == "__main__":
    main()
