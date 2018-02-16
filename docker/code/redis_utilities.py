#!/usr/bin/env python3

"""Utiliites for interacting with the KnowEnG Redis db through python.

Contains module functions::

    get_database(args=None)
    import_ensembl(alias, args=None)
    conv_gene(rdb, foreign_key, hint, taxid)


"""

import json
import os
from argparse import ArgumentParser
import subprocess
import csv
import redis
import config_utilities as cf

MGET_CHUNK = 100

def deploy_container(args=None):
    """Deplays a container with marathon running Redis using the specified
    args.

    This replaces the placeholder args in the json describing how to deploy a
    container running Redis with those supplied in the users arguements.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults
    """
    if args is None:
        args = cf.config_args()
    deploy_dir = os.path.join(args.working_dir, args.logs_path, 'marathon_jobs')
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)
    template_job = os.path.join(args.working_dir, args.code_path,
                                'marathon', 'redis.json')
    with open(template_job, 'r') as infile:
        deploy_dict = json.load(infile)
    deploy_dict["id"] = os.path.basename(args.redis_dir)
    deploy_dict["cmd"] = "redis-server --appendonly yes --requirepass " + \
                        args.redis_pass + " --port " + args.redis_port
    deploy_dict["cpus"] = float(args.redis_cpu)
    deploy_dict["mem"] = int(args.redis_mem)
    if args.redis_curl:
        deploy_dict["constraints"] = [["hostname", "CLUSTER", args.redis_curl]]
    else:
        deploy_dict["constraints"] = []
    deploy_dict["container"]["volumes"][0]["hostPath"] = args.redis_dir
    out_path = os.path.join(deploy_dir, "kn_redis-" + args.redis_port +'.json')
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
        args = cf.config_args()
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
        args = cf.config_args()
    rdb = get_database(args)
    map_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
    with open(os.path.join(map_dir, alias + '_all.json')) as infile:
        map_dict = json.load(infile)
    for key in map_dict:
        (taxid, _, _, hint, foreign_key) = key.split('::')
        hint = hint.upper()
        ens_id = map_dict[key].upper()
        foreign_key = foreign_key.upper()

        keystr = 'unique::' + foreign_key
        rkey = rdb.getset(keystr, ens_id)
        if rkey is not None and rkey.decode() != ens_id:
            rdb.set(keystr, 'unmapped-many')

        keystr = 'hint::' + foreign_key + '::' + hint
        rkey = rdb.getset(keystr, ens_id)
        if rkey is not None and rkey.decode() != ens_id:
            rdb.set(keystr, 'unmapped-many')

        keystr = 'taxon::' + foreign_key + '::' + taxid
        rkey = rdb.getset(keystr, ens_id)
        if rkey is not None and rkey.decode() != ens_id:
            rdb.set(keystr, 'unmapped-many')

        keystr = 'triplet::' + foreign_key + '::' + taxid + '::' + hint
        rkey = rdb.getset(keystr, ens_id)
        if rkey is not None and rkey.decode() != ens_id:
            rdb.set(keystr, 'unmapped-many')

        if hint == 'WIKIGENE': # to replace integer aliases with strings
            try:
                int(rdb.get('::'.join(['stable', ens_id, 'alias'])))
            except TypeError:
                rdb.set('::'.join(['stable', ens_id, 'alias']), foreign_key)
            except ValueError:
                pass
            else:
                rdb.set('::'.join(['stable', ens_id, 'alias']), foreign_key)

def import_gene_nodes(node_table, args=None):
    """Import gene node metadata into redis.
    """
    if args is None:
        args = cf.config_args()
    rdb = get_database(args)
    for row in node_table:
        node_id, node_desc, node_type = row
        node_id = node_id.upper()
        rdb.set('::'.join(['stable', node_id, 'desc']), node_desc)
        rdb.set('::'.join(['stable', node_id, 'type']), node_type)

def import_node_meta(nmfile, args=None):
    """Import node metadata into redis.
    """
    if args is None:
        args = cf.config_args()
    rdb = get_database(args)
    with open(nmfile) as infile:
        reader = csv.reader(infile, delimiter='\t')
        for row in reader:
            node_id, nm_type, nm_value = row
            node_alias = node_id
            node_desc = node_id
            if nm_type == 'orig_id':
                node_alias = nm_value
            elif nm_type == 'orig_desc':
                node_desc = nm_value
            elif nm_type == 'biotype':
                rkey = rdb.getset('::'.join(['stable', node_id, 'biotype']), nm_value)
                if rkey is not None and rkey.decode() != nm_value:
                    rdb.set('::'.join(['stable', node_id, 'biotype']), rkey)
            elif nm_type == 'taxid':
                rkey = rdb.getset('::'.join(['stable', node_id, 'taxid']), nm_value)
                if rkey is not None and rkey.decode() != nm_value:
                    rdb.set('::'.join(['stable', node_id, 'taxid']), rkey)
            else:
                continue

            rkey = rdb.getset('::'.join(['stable', node_id, 'type']), 'Property')
            if rkey is not None and rkey.decode() != 'Property':
                rdb.set('::'.join(['stable', node_id, 'type']), rkey)

            rkey = rdb.getset('::'.join(['stable', node_id, 'alias']), node_alias)
            if rkey is not None and rkey.decode() != node_alias and rkey.decode() != node_id:
                rdb.set('::'.join(['stable', node_id, 'alias']), rkey)
            rkey = rdb.getset('::'.join(['stable', node_id, 'desc']), node_desc)
            if rkey is not None and rkey.decode() != node_desc and rkey.decode() != node_id:
                rdb.set('::'.join(['stable', node_id, 'desc']), rkey)

def get_node_info(rdb, fk_array, ntype, hint, taxid):
    """Uses the redis database to convert a node alias to KN internal id

    Figures out the type of node for each id in fk_array and then returns
    all of the metadata associated or unmapped-*

    Args:
        rdb (redis object): redis connection to the mapping db
        fk_array (list): the array of foreign gene identifers to be translated
        ntype (str): 'Gene' or 'Property' or None
        hint (str): a hint for conversion
        taxid (str): the species taxid, None if unknown

    Returns:
        list: list of lists containing 5 col info for each mapped gene
    """
    hint = None if hint == '' or hint is None else hint.upper()
    taxid = None if taxid == '' or taxid is None else str(taxid)
    if ntype == '':
        ntype = None

    if ntype is None:
        res_arr = rdb.mget(['::'.join(['stable', str(fk), 'type']) for fk in fk_array])
        fk_prop = [fk for fk, res in zip(fk_array, res_arr) if res is not None
                   and res.decode() == 'Property']
        fk_gene = [fk for fk, res in zip(fk_array, res_arr) if res is not None
                   and res.decode() == 'Gene']
        if fk_prop and fk_gene:
            raise ValueError("Mixture of property and gene nodes.")
        ntype = 'Property' if fk_prop else 'Gene'

    if ntype == "Gene":
        stable_array = conv_gene(rdb, fk_array, hint, taxid)
    elif ntype == "Property":
        stable_array = fk_array
    else:
        raise ValueError("Invalid ntype")

    return list(zip(fk_array, *node_desc(rdb, stable_array)))


def conv_gene(rdb, fk_array, hint, taxid):
    """Uses the redis database to convert a gene to ensembl stable id

    This checks first if there is a unique name for the provided foreign key.
    If not it uses the hint and taxid to try and filter the foreign key
    possiblities to find a matching stable id.

    Args:
        rdb (redis object): redis connection to the mapping db
        fk_array (list): the foreign gene identifers to be translated
        hint (str): a hint for conversion
        taxid (str): the species taxid, 'unknown' if unknown

    Returns:
        str: result of searching for gene in redis DB
    """
    hint = None if hint == '' or hint is None else hint.upper()
    taxid = None if taxid == '' or taxid is None else str(taxid)

    #use ensembl internal uniprot mappings
    if hint == 'UNIPROT' or hint == 'UNIPROTKB':
        hint = 'UNIPROT_GN'

    ret_stable = ['unmapped-none'] * len(fk_array)

    def replace_none(ret_st, pattern):
        """Search redis for genes that still are unmapped
        """
        curr_none = [i for i in range(len(fk_array)) if ret_st[i] == 'unmapped-none']
        while curr_none:
            temp_curr_none = curr_none[:MGET_CHUNK]
            curr_none = curr_none[MGET_CHUNK:]
            vals_array = rdb.mget([pattern.format(str(fk_array[i]).upper(), taxid, hint)
                                   for i in temp_curr_none])
            for i, val in zip(temp_curr_none, vals_array):
                if val is None:
                    continue
                ret_st[i] = val.decode()

    if hint is not None and taxid is not None:
        replace_none(ret_stable, 'triplet::{0}::{1}::{2}')
    if taxid is not None:
        replace_none(ret_stable, 'taxon::{0}::{1}')
    if hint is not None:
        replace_none(ret_stable, 'hint::{0}::{2}')
    if taxid is None:
        replace_none(ret_stable, 'unique::{0}')
    return ret_stable


def node_desc(rdb, stable_array):
    """Uses the redis database to find metadata about node given its stable id

    Return all metadata for each element of stable_array

    Args:
        rdb (redis object): redis connection to the mapping db
        stable_array (str): the array of stable identifers to be searched

    Returns:
        list: list of lists containing 4 col info for each mapped node
    """
    ret_type = ["None"] * len(stable_array)
    ret_alias = list(stable_array)
    ret_desc = list(stable_array)
    st_map_idxs = [idx for idx, st in enumerate(stable_array) if not st.startswith('unmapped')]
    if st_map_idxs:
        vals_array = rdb.mget(['::'.join(['stable', stable_array[i], 'type']) for i in st_map_idxs])
        for i, val in zip(st_map_idxs, vals_array):
            if val is None:
                continue
            ret_type[i] = val.decode()
        vals_array = rdb.mget(['::'.join(['stable', stable_array[i], 'alias'])
                               for i in st_map_idxs])
        for i, val in zip(st_map_idxs, vals_array):
            if val is None:
                continue
            ret_alias[i] = val.decode()
        vals_array = rdb.mget(['::'.join(['stable', stable_array[i], 'desc']) for i in st_map_idxs])
        for i, val in zip(st_map_idxs, vals_array):
            if val is None:
                continue
            ret_desc[i] = val.decode()
    return stable_array, ret_type, ret_alias, ret_desc


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
