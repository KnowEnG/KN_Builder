#!/usr/bin/env python3

"""Utiliites for interacting with the KnowEnG Redis db through python.

Contains module functions::

    get_database(args=None)
    import_ensembl(alias, args=None)
    conv_gene(rdb, foreign_key, hint, taxid)
    import_mapping(map_dict, args=None)

"""

import config_utilities as cf
import redis
import json
import os
from argparse import ArgumentParser
import subprocess

def deploy_container(args=None):
    """Deplays a container with marathon running Redis using the specified
    args.
    
    This replaces the placeholder args in the json describing how to deploy a 
    container running Redis with those supplied in the users arguements.
    
    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    deploy_dir = os.path.join(args.working_dir, args.logs_path, 'marathon_jobs')
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)
    template_job = os.path.join(args.working_dir, args.code_path, 
                                'dockerfiles', 'marathon', 'redis.json')
    with open(template_job, 'r') as infile:
        deploy_dict = json.load(infile)
    deploy_dict["id"] = os.path.basename(args.redis_dir)
    deploy_dict["cmd"] ="redis-server --appendonly yes --requirepass " + \
                        args.redis_pass
    deploy_dict["cpus"] = float(args.redis_cpu)
    deploy_dict["mem"] = int(args.redis_mem)
    if args.redis_curl:
        deploy_dict["constraints"] = [["hostname", "CLUSTER", args.redis_curl]]
    else:
        deploy_dict["constraints"] = []
    deploy_dict["container"]["volumes"][0]["hostPath"] = args.redis_dir
    deploy_dict["container"]["docker"]["portMappings"][0]["hostPort"] = int(args.redis_port)
    out_path = os.path.join(deploy_dir, "p1redis-" + args.redis_port +'.json')
    with open(out_path, 'w') as outfile:
        outfile.write(json.dumps(deploy_dict))
    job= 'curl -X POST -H "Content-type: application/json" ' + args.marathon + " -d '"
    job += json.dumps(deploy_dict) + "'"
    if not args.test_mode:
        try:
            subprocess.check_output(job, shell=True)
        except subprocess.CalledProcessError as ex1:
            print(ex1.output)
    else:
        print(job)

def get_database(args=None):
    """Returns a Redis database connection.

    This returns a Redis database connection access to its functions if the
    module is imported.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    Returns:
        StrictRedis: a redis connection object
    """
    if args is None:
        args=cf.config_args()
    return redis.StrictRedis(host=args.redis_host, port=args.redis_port,
                             password=args.redis_pass)

def import_ensembl(alias, args=None):
    """Imports the ensembl data for the provided alias into the Redis database.

    This stores the foreign key to ensembl stable ids in the Redis database.
    It uses the all mappings dictionary created by mysql.query_all_mappings
    for alias. This then iterates through each foreign_key. If the foreign_key
    has not been seen before, it sets unique:foreign_key as the stable id. If
    the key has been seen before and maps to a different ensembl stable id, it
    sets the value for unique:foreign_key as unmapped:many. In each case, it
    sets the value of taxid:hint:foreign_key as the stable_id, and appends
    taxid:hint to the set with foreign_key as the key.

    Args:
        alias (str): An alias defined in ensembl.aliases.
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    rdb = get_database(args)
    map_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
    with open(os.path.join(map_dir, alias + '_all.json')) as infile:
        map_dict = json.load(infile)
    for key in map_dict:
        (taxid, _, _, hint, foreign_key) = key.split('::')
        hint = hint.upper()
        ens_id = map_dict[key].encode().upper()
        foreign_key = foreign_key.upper()
        rkey = rdb.getset('unique::' + foreign_key, ens_id)
        if rkey is not None and rkey != ens_id:
            rdb.set('unique::' + foreign_key, 'unmapped-many')
        rdb.sadd(foreign_key, '::'.join([taxid, hint]))
        rdb.set('::'.join([taxid, hint, foreign_key]), ens_id)

def conv_gene(rdb, foreign_key, hint, taxid):
    """Uses the redis database to convert a gene to enesmbl stable id

    This checks first if there is a unique name for the provided foreign key.
    If not it uses the hint and taxid to try and filter the foreign key
    possiblities to find a matching stable id.

    Args:
        rdb (redis object): redis connection to the mapping db
        foreign_key (str): the foreign gene identifer to be translated
        hint (str): a hint for conversion
        taxid (str): the species taxid, 'unknown' if unknown

    Returns:
        str: result of seaching for gene in redis DB
    """
    hint = hint.upper()
    #use ensembl internal uniprot mappings
    if hint == 'UNIPROT' or hint == 'UNIPROTKB':
        hint = 'UNIPROT_GN'
    foreign_key = foreign_key.upper()
    unique = rdb.get('unique::' + foreign_key)
    if unique is None:
        return 'unmapped-none'
    if unique != 'unmapped-many'.encode():
        return unique.decode()
    mappings = rdb.smembers(foreign_key)
    taxid_match = list()
    hint_match = list()
    both_match = list()
    for taxid_hint in mappings:
        taxid_hint = taxid_hint.decode()
        taxid_hint_key = '::'.join([taxid_hint, foreign_key])
        taxid_hint = taxid_hint.split('::')
        if len(taxid_hint) < 2: # species key in redis
            continue
        if taxid == taxid_hint[0] and hint in taxid_hint[1]:
            both_match.append(taxid_hint_key)
        if taxid == taxid_hint[0]:
            taxid_match.append(taxid_hint_key)
        if hint in taxid_hint[1] and len(hint):
            hint_match.append(taxid_hint_key)
    if both_match:
        both_ens_ids = set(rdb.mget(both_match))
        if len(both_ens_ids) == 1:
            return both_ens_ids.pop().decode()
    if taxid_match:
        taxid_ens_ids = set(rdb.mget(taxid_match))
        if len(taxid_ens_ids) == 1:
            return taxid_ens_ids.pop().decode()
    if hint_match:
        hint_ens_ids = set(rdb.mget(hint_match))
        if len(hint_ens_ids) == 1:
            return hint_ens_ids.pop().decode()
    return 'unmapped-many'

def import_mapping(map_dict, args=None):
    """Imports the property mapping data into the Redis database.

    This stores the original id to KnowNet ids in the Redis database.

    Args:
        map_dict (dict): An dictionary containing all mapping info.
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args=cf.config_args()
    rdb = get_database(args)
    for orig_id in map_dict:
        rkey = rdb.getset('property::' + orig_id, map_dict[orig_id])
        if rkey is not None and rkey != map_dict[orig_id]:
            rdb.set('property::' + orig_id, 'unmapped-many')
        rdb.sadd(orig_id, map_dict[orig_id])

def main():
    """Deploy a Redis container using marathon with the provided command line
    arguements. 
    
    This uses the provided command line arguments and the defaults found in 
    config_utilities to launch a Redis docker container using marathon.
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    deploy_container(args)
    
if __name__ == "__main__":
    main()