"""Utiliites for interacting with the KnowEnG Redis db through python.

Classes:


Functions:


Variables:
"""

import config_utilities as cf
import redis
import json
import os

def import_ensembl(alias):
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

    Returns:
    """
    rdb = redis.StrictRedis(host=cf.DEFAULT_REDIS_URL,
        port=cf.DEFAULT_REDIS_PORT, db=0)
    map_dir = os.sep + cf.DEFAULT_MAP_PATH
    if os.path.isdir(cf.DEFAULT_LOCAL_BASE):
        map_dir = cf.DEFAULT_LOCAL_BASE + map_dir
    with open(os.path.join(map_dir, alias + '_all.json')) as infile:
        map_dict = json.load(infile)
    for key in map_dict:
        (taxid, hint, foreign_key) = key.split('::')
        hint = hint.upper()
        ens_id = map_dict[key].encode()
        rkey = rdb.get('unique::' + foreign_key)
        if rkey is None:
            rdb.set('unique::' + foreign_key, ens_id)
        elif rkey != ens_id and rkey != 'unmapped-many'.encode():
            rdb.set('unique::' + foreign_key, 'unmapped-many')
        rdb.sadd(foreign_key, '::'.join([taxid, hint]))
        rdb.set('::'.join([taxid, hint, foreign_key]), ens_id)
