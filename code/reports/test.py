#!/usr/bin/env python3

"""This module implements some reporting of mapping failures in the KnowEnG pipeline.

Assumptions:
Only errors are unmapped, marked in status file.
Directory layout.
"""

import multiprocessing
import json
import itertools
import collections
import os
import pprint
import sys


def process_chunk(indir, chunkid):
    """Get amounts of failed mappings for a chunk.

    Keywork arguments:
    indir -- the directory containing the chunks directory
    chunkid -- the number of the chunk to process

    Return value:
    A tuple of the number of failures per status_desc and per node id

    """
    db, species = indir.rstrip('/').split('/')[-2:]
    inf = open("{}/chunks/{}.{}.status.{}.txt".format(indir, db, species, chunkid), 'r')
    hash_to_table = {i[11]: tuple(i[1:9]) for i in (i.strip().split('\t') for i in open("{}/chunks/{}.{}.table.{}.txt".format(indir, db, species, chunkid), 'r'))}

    d = collections.Counter()
    bad = set()
    for line in inf:
        line = line.strip().split('\t')
        d[line[-1]] += 1
        if line[1].startswith('unmapped'):
            bad.add((line[0], 0, line[1]))
        if line[2].startswith('unmapped'):
            bad.add((line[0], 4, line[2]))

    return d, collections.Counter((hash_to_table[i[0]][i[1]], i[2]) for i in bad)


def get_percents(results):
    if type(results) == collections.Counter:
        total = sum(results.values())
        return {k: v/total for k, v in results.items()}
    elif type(results) == list:
        return
    else:
        for k, v in results.items():
            if k == "_sum":
                results["_sum"] = get_percents(v)
            else:
                get_percents(v)


def print_results(results):
    sums = sum((x[0] for x in results), collections.Counter())
    most = sum((x[1] for x in results), collections.Counter()).most_common()
    most_flat = [i[0] + (i[1],) for i in most]
    return {"_most": most_flat, "_sum": sums}


def recurse(dir, pool):
    metadata_f = os.path.join(dir, "file_metadata.json")
    if os.path.exists(metadata_f):
        try:
            numchunks = json.load(open(metadata_f))["num_chunks"]
            if numchunks == 0: raise ValueError()
        except (KeyError, ValueError):
            return {}
        return pool.starmap_async(process_chunk, zip(itertools.repeat(dir), range(1, numchunks+1)))
    else:
        return {i: recurse(i, pool) for i in filter(os.path.isdir, (os.path.join(dir, f) for f in os.listdir(dir)))}


def recurse_results(results):
    if type(results) == multiprocessing.pool.MapResult:
        return print_results(results.get())
    else:
        for key, subresult in results.items():
            results[key] = recurse_results(subresult)
        results["_sum"] = sum((i.get("_sum", collections.Counter()) for i in results.values()), collections.Counter())
        return results


def get_unmapped(results):
    ret = {}
    for k, v in results.items():
        if '_most' in v:
            ret.update({k: v["_most"]})
        elif '_sum' in v:
            ret.update(get_unmapped(v))
    return ret


def main(input, numproc = None, numlargest = None):
    """Run process_chunk on each input chunk.

    Keyword arguments:
    input -- list of input directories; each should contain a chunks subdirectory
    numproc -- the number of child processes to spawn
    numlargest -- the number of node ids with the most errors to print out

    Return value:
    A number indicating success (0) or failure (>0), which can be used as a return value

    """
    if numlargest is None: numlargest = 5
    pool = multiprocessing.Pool(numproc)

    results = recurse(input, pool)
    results = recurse_results(results)
    get_percents(results)

    json.dump({
        "percents": sorted([(k, v["_sum"]) for k, v in results.items() if k != "_sum"], key=lambda x: x[1].get("mapped", 0), reverse=True),
        "unmapped": {k: v[:min(len(v),5)] for k, v in get_unmapped(results).items()}
        }, fp=sys.stdout)

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Report on success and failure mapping.")
    parser.add_argument("input", type=str, help="Input directory.")
    parser.add_argument("-p", "--numproc", type=int, help="Number of child processes to spawn.")
    parser.add_argument("-l", "--numlargest", type=int, help="Number of largest unmapped to show.")

    args = parser.parse_args()
    exit(main(**vars(args)))
