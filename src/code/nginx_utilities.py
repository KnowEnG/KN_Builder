#!/usr/bin/env python3

"""Utiliites for interacting with the KnowEnG Nginx db through python.

Contains module functions::


"""

import json
import os
import subprocess
from argparse import ArgumentParser
import config_utilities as cf

def deploy_container(args=None):
    """Deplays a container with marathon running nginx using the specified
    args.

    This replaces the placeholder args in the json describing how to deploy a
    container running Nginx with those supplied in the users arguements.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    deploy_dir = os.path.join(args.working_dir, args.logs_path, 'marathon_jobs')
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)
    template_job = os.path.join(args.working_dir, args.code_path,
                                'marathon', 'nginx.json')
    with open(template_job, 'r') as infile:
        deploy_dict = json.load(infile)
    deploy_dict["id"] = os.path.basename(args.nginx_dir)
    if args.nginx_curl:
        deploy_dict["constraints"] = [["hostname", "CLUSTER", args.nginx_curl]]
    else:
        deploy_dict["constraints"] = []
    deploy_dict["container"]["volumes"][0]["hostPath"] = args.nginx_dir
    docs_path = os.path.join(args.working_dir, 'KnowNet_Pipeline', 'docs', \
                            '_build', 'html')
    deploy_dict["container"]["volumes"][1]["hostPath"] = docs_path
    conf_path = os.path.join(args.working_dir, args.code_path, 'nginx', args.nginx_conf)
    deploy_dict["container"]["volumes"][2]["hostPath"] = conf_path
    deploy_dict["container"]["docker"]["portMappings"][0]["hostPort"] = int(args.nginx_port)
    out_path = os.path.join(deploy_dir, "kn_nginx-" + args.nginx_port +'.json')
    with open(out_path, 'w') as outfile:
        outfile.write(json.dumps(deploy_dict))
    job = 'curl -X POST -H "Content-type: application/json" ' + args.marathon + " -d '"
    job += json.dumps(deploy_dict) + "'"
    if not args.test_mode:
        try:
            subprocess.check_output(job, shell=True)
        except subprocess.CalledProcessError as ex1:
            print(ex1.output)
    else:
        print(job)

def main():
    """Deploy a Nginx container using marathon with the provided command line
    arguements.

    This uses the provided command line arguments and the defaults found in
    config_utilities to launch a Nginx docker container using marathon.
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    deploy_container(args)

if __name__ == "__main__":
    main()
