"""Utiliites for Jobs class which store all important information for each job to run

Classes:
    Jobs: Stores all important information for each job to run on cluster

Contains module functions::

    queue_starter_job(args, jobname='starter-jobname', dummy=1)
    run_job_step(args, job_type, tmpdict)

    run_local_fetch(args)
    curl_handler(args, jobname, job_str)
    chronos_parent_str(parentlist)

Attributes:
    CURL_PREFIX (list): parts of the chronos curl command
"""

import os
import subprocess
import json
import stat

CURL_PREFIX = ["curl", "-i", "-L", "-H", "'Content-Type: application/json'",
               "-X", "POST"]

class Job:
    """Base class for each job to be run in pipeline.

    This Job class provides attributes and default functions to store information
    about and perform operations on job.

    Attributes:
        jobtype (str): the type of job to be referenced in components.json
        jobname (str): name of job as appears on chronos
        tmpdict (dict): dictionary of default tmp variable substitutions
        cjobfile (str): chronos local file name of json job descriptor
        cjobstr (str): contents of json job descriptor as single string.
        args (namespace): command line arguments and default arguments to method
    """
    def __init__(self, jobtype, args):
        """Init a Job object with the provided parameters.

        Constructs a Job object with the provided parameters.

        Args:
            jobtype (str): the type of job to be referenced in components.json
            args (namespace): command line arguments and default arguments to method
        """
        self.jobtype = jobtype
        self.args = args
        self.jobname = jobtype + "_job"
        self.cjobfile = 'missing.json'
        # read in dummy template
        self.cjobstr = ""
        with open(os.path.join(self.args.working_dir, args.code_path, "template",
                               "job_template.json"), 'r') as infile:
            self.cjobstr = infile.read(10000)
        # read in job dictionaries
        jobsdesc = ""
        with open(os.path.join(self.args.working_dir, args.code_path, "template",
                               "components.json"), 'r') as infile:
            jobsdesc = json.load(infile)
        # prepare volume mount
        vmntstr = '{"containerPath": "TMPWORKDIR", "hostPath":"TMPWORKDIR", "mode":"RW"}'
        if self.args.working_dir != self.args.storage_dir:
            vmntstr += ', {"containerPath": "TMPSHAREDIR", "hostPath":"TMPSHAREDIR", "mode":"RW"}'
        # replace global dummy values with job specific ones
        self.tmpdict = jobsdesc[jobtype]
        self.tmpdict["TMPVMNTSTR"] = vmntstr
        self.replace_jobtmp(self.tmpdict)
    def replace_jobtmp(self, tmpdict):
        """Replaces temporary strings in self.cjobstr with specific values

        This loops through all keys in tmpdict and replaces any placeholder matches
        in self.cjobstr with the key values.  Also, adds tmpdict to self.tmpdict.

        Args:
            tmpdict (dict): dictionary of default tmp variable substitutions

        Returns:
        """
        envstr = str(self.tmpdict.get("TMPENV", "[]"))
        for key in tmpdict:
        #    print(key + " " +  str(tmpdict[key]) )
            if key == 'TMPJOB':
                self.jobname = tmpdict[key]
            self.cjobstr = self.cjobstr.replace(key, str(tmpdict[key]))
            envstr = envstr.replace(key, str(tmpdict[key]))
            self.tmpdict[key] = tmpdict[key]
        self.tmpdict['TMPENV'] = envstr
    def print_chronos_job(self):
        """Prints out job description to .json file

        This creates a directory and in it prints a .json file containing self.cjobstr.
        It saves the created file as self.cjobfile

        Args:

        Returns:
        """
        jobs_dir = os.path.join(self.args.working_dir, self.args.logs_path, 'chron_jobs')
        if not os.path.exists(jobs_dir):
            os.makedirs(jobs_dir)
        cjobfile = jobs_dir + os.sep + self.jobname + ".json"
        self.cjobfile = cjobfile
        with open(cjobfile, 'w') as outfile:
            outfile.write(self.cjobstr)
    def run_local_job(self):
        """prints and runs the job in the local environment

        Using the args, tmpdict, and cjobstr create a command line call to
        executes the job
        """
        jobjson = json.loads(self.cjobstr)
        command = jobjson["command"]
        print(command)
        if not self.args.test_mode:
#           subprocess.call(command, shell=True)
            try:
                subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError as ex1:
                print(ex1.output)
    def run_docker_job(self):
        """runs the job locally using docker

        Using the args, tmpdict, and cjobstr create a command line call to docker
        run that executes the job and removes itself
        """
        jobjson = json.loads(self.cjobstr)
        envvars = json.loads(self.tmpdict.get("TMPENV", "[]"))
        envstr = ""
        vmntstr = "-v " + self.args.working_dir + ":" + self.args.working_dir
        if self.args.working_dir != self.args.storage_dir:
            vmntstr += " -v " + self.args.storage_dir + ":" + self.args.storage_dir
        for env in envvars:
            envstr += ' -e ' + env['variable'] + '=' + env['value']
        docker_cmd = ["docker", "run", "--name", jobjson["name"], "--rm=true",
                      vmntstr, self.tmpdict["TMPIMG"], jobjson["command"]]
        print("\n"+" ".join(docker_cmd))
        if not self.args.test_mode:
#           subprocess.call(' '.join(docker_cmd), shell=True)
            try:
                subprocess.check_output(' '.join(docker_cmd), shell=True)
            except subprocess.CalledProcessError as ex1:
                print(ex1.output)
    def queue_chronos_job(self):
        """puts the job on the chronos queue

        Using the chronos url from args.chronos, this creates a tmp .sh job that
        runs the curl statement to sent job to chronos
        """
        self.print_chronos_job()
        curl_cmd = list(CURL_PREFIX)
        curl_cmd.extend(["-d@" + self.cjobfile])
        if self.tmpdict["TMPLAUNCH"].find("schedule") > -1:
            curl_cmd.extend([self.args.chronos + "/scheduler/iso8601"])
        else:
            curl_cmd.extend([self.args.chronos + "/scheduler/dependency"])
        print(" ".join(curl_cmd))
        print(self.cjobstr)
        if not self.args.test_mode:
            #subprocess.call(curl_cmd, shell=True)
            shfile = self.cjobfile.replace(".json", ".sh")
            with open(shfile, 'w') as outfile:
                outfile.write(" ".join(curl_cmd))
            os.chmod(shfile, stat.S_IRWXU)
            subprocess.call(['sh', "-c", shfile])
            os.remove(shfile)
    def run_job(self):
        """Sends job to chronos job queue

        Using the chronos url from args.chronos, this creates a tmp .sh job that
        runs the curl statement to sent job to chronos
        """
        if self.args.chronos == "LOCAL":
            self.run_local_job()
        elif self.args.chronos == "DOCKER":
            self.run_docker_job()
        else:
            self.queue_chronos_job()

def queue_starter_job(args, jobname='starter-jobname', dummy=1):
    """Queues a starter job.

    If dummy=1, creates and queues a dummy job that will never run, else it
    queues a simple job with a single print statement that will run immediately
    on which other jobs will depend

    Args:
        jobstr (str): contents of json job descriptor as single string.
        dummy (bool): 1, queue jobs that does not run, 0, queue job that does


    Returns: Job object
    """
    myjob = Job('starter', args)
    if args.chronos == "LOCAL":
        return myjob
    elif args.chronos == "DOCKER":
        return myjob

    tmpdict = {'TMPLAUNCH': r'"schedule": "R1\/\/P3M"',
               'TMPMSG': 'date | sed \\"s#^#TMPJOB begun #g\\"'}
    if dummy == 1:
        tmpdict['TMPLAUNCH'] = r'"schedule": "R1\/2200-01-01T06:00:00Z\/P3M"'
        tmpdict['TMPMSG'] = 'echo \\"TMPJOB was not supposed to run\\"'
        tmpdict['TMPJOB'] = jobname
    myjob.replace_jobtmp(tmpdict)
    myjob.queue_chronos_job()
    return myjob

def run_job_step(args, job_type, tmpdict):
    """Creates and runs a job.

    Using the tmpdict description of the job will create and queue a new job
    that runs when its dependencies finish in the correct mode

    Args:
        args (namespace): arguments from main_parse_args().
        job_type (string): type of job to be created
        tmpdict (dict): dictionary with all of the arguments values required

    Returns: Job object
    """
    myjob = Job(job_type, args)
    myjob.replace_jobtmp(tmpdict)
    myjob.run_job()
    return myjob

def chronos_parent_str(parentlist):
    """Returns correct string for parent dependencies.

    Formatting of returned string depends on number of parents

    Args:
        parentlist (list): names of parent jobs

    Returns: string
    """
    return '"parents": {0}'.format(str(parentlist).replace("'", "\""))
