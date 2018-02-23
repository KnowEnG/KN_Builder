from argparse import ArgumentParser
from datetime import datetime, timezone
import os
import sys
import csv
import subprocess
import yaml
#import numpy as np
#import scipy.sparse as ss
from collections import defaultdict

import config_utilities as cf
import redis_utilities as ru
import mysql_utilities as mu
import sanitize_utilities as su

def get_gg(db, et, taxon):
    """Get gene-gene nodes.
    """
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num "
                  "FROM status s JOIN node_species n1 ON s.n1_id = n1.node_id "
                  "JOIN node_species n2 ON s.n2_id = n2.node_id "
                  "JOIN raw_line rl ON s.line_hash = rl.line_hash "
                  "WHERE s.et_name = '{}' AND n1.taxon = {} AND n2.taxon = {} "
                  "AND s.status = 'production';".format(et, taxon, taxon))

def get_pg(db, et, taxon):
    """Get property-gene nodes.
    """
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num "
                  "FROM status s JOIN node_species n2 ON s.n2_id = n2.node_id "
                  "JOIN raw_line rl ON s.line_hash = rl.line_hash "
                  "WHERE s.et_name = '{}' AND n2.taxon = {} "
                  "AND s.status = 'production';".format(et, taxon))

def num_connected_components(edges, nodes):
    """Count the number of connected components in a graph given the edges and the nodes.
    """
    nodes = list(nodes)
    rev_nodes = {v: i for i, v in enumerate(nodes)}
    row = []
    col = []
    for edge in edges:
        r, c = edge[:2]
        row.append(rev_nodes[r])
        col.append(rev_nodes[c])
#    mat = ss.coo_matrix((np.ones(len(edges)), (row, col)), shape=(len(nodes), len(nodes)))
#    num, _ = ss.csgraph.connected_components(mat)
    return -1
    return num

def figure_out_class(db, et):
    """Determines the class and bidirectionality of the edge_type.
    """
    return db.run("SELECT n1_type, bidir FROM edge_type WHERE et_name = '{}'".format(et))[0]

def norm_edges(edges, args):
    """Normalizes and cleans edges according to the specified arguments.
    """
    lines = []
    lines.append(len(edges))
    if args.make_unweighted:
        edges = su.make_network_unweighted(edges, 2)
    lines.append(len(edges))
    if args.make_undirected: #TODO: less important, yes, no, auto
        edges = su.make_network_undirected(edges)
    lines.append(len(edges))
    edges = su.sort_network(edges)
    lines.append(len(edges))
    edges = su.drop_duplicates_by_type_or_node(edges, 0, 1, 3)
    lines.append(len(edges))
    if args.make_undirected: #TODO: less important, yes, no, auto
        edges = su.upper_triangle(edges, 0, 1)
    lines.append(len(edges))
    edges = su.normalize_network_by_type(edges, 3, 2) #TODO: none, all, type
    lines.append(len(edges))
    return edges, lines

def convert_nodes(args, nodes):
    """Uses redis_utilities to convert a set of nodes.
    """
    rdb = ru.get_database(args)
    return ru.get_node_info(rdb, nodes, None, None, args.species)

def get_sources(edges):
    """Given a list of edges, determines the set of sources included.
    """
    return set(edge[4] for edge in edges)

def get_log_query(sources):
    return "SELECT filename, info_type, info_value FROM log WHERE filename IS NULL"

def get_metadata(db, edges, nodes, lines, sp, et, args):
    """Retrieves the metadata for a subnetwork.
    """

    sources = get_sources(edges)
    print(sources)
    datasets = {}
    for source in sources:
        file_id, remote_url, remote_date, remote_version, source_url, \
            image, reference, date_downloaded, checksum, pmid, license = \
            db.run("SELECT file_id, remote_url, remote_date, remote_version, source_url, image, "
                   "reference, date_downloaded, checksum, pmid, license FROM raw_file "
                   "WHERE file_id = '{}'".format(source))[0]
        datasets[file_id] = {"source_url": source_url, "image": image, "reference": reference,
                             "download_url": remote_url, "remote_version": remote_version,
                             "remote_date": datetime.utcfromtimestamp(float(remote_date)),
                             "download_date": date_downloaded, "file_checksum": checksum,
                             "pubmed": pmid, "license": license}

    sciname, = db.run("SELECT sp_sciname FROM species WHERE taxon = '{}'".format(sp))[0]
    n1_type, n2_type, bidir, et_desc, sc_desc, sc_best, sc_worst = \
            db.run("SELECT n1_type, n2_type, bidir, et_desc, sc_desc, sc_best, sc_worst "
                   "FROM edge_type WHERE et_name = '{}'".format(et))[0]

    num_prop, num_gene, num_none = 0, 0, 0
    for _, _, typ, _, _ in nodes:
        if typ == "Property":
            num_prop += 1
        elif typ == "Gene":
            num_gene += 1
        elif typ == "None":
            num_none += 1
        else:
            raise ValueError("Invalid type: {}".format(type))

    build = defaultdict(dict)
    build["export"] = {"command": sys.argv, "arguments": args, "date": datetime.now(timezone.utc),
                        "revision": str(subprocess.check_output(["git", "describe", "--always"]).strip())}
    query = get_log_query(sources)
    for f, t, k in db.run(query):
        build[t][f] = k
    build = dict(build)

    return {"id": ".".join([sp, et]), "datasets": datasets, "build_metadata": build,
            "species": {"taxon_identifier": sp, "scientific_name": sciname},
            "edge_type": {"id": et, "n1_type": n1_type, "n2_type": n2_type, "type_desc": et_desc,
                          "score_desc": sc_desc, "score_best": sc_best, "score_worst": sc_worst,
                          "bidirectional": bidir},
            "data": {"num_edges": len(edges), "num_nodes": len(nodes), "num_prop_nodes": num_prop,
                     "num_gene_nodes": num_gene, "num_connected_components":
                     #num_connected_components(edges, [n[0] for n in nodes]),
                     0,
                     "density": 2*len(edges)/(len(nodes)*(len(nodes)-1))}}

def should_skip(cls, res):
    """Determine if the subnetwork is especially small, and if we should skip it.
    """
    return (cls == 'Property' and len(res) < 4000) or (cls == 'Gene' and len(res) < 125000)

def main():
    """Parses arguments and then exports the specified subnetworks.
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    parser = su.add_config_args(parser)
    parser.add_argument("-e", "--edge_type", help="Edge type")
    parser.add_argument("-s", "--species", help="Species")
    args = parser.parse_args()

    db = mu.get_database(args=args)
    db.use_db("KnowNet")

    cls, bidir = figure_out_class(db, args.edge_type)
    edges_fn = '{}.{}.edge'.format(args.species, args.edge_type)
    nodes_fn = '{}.{}.node_map'.format(args.species, args.edge_type)
    meta_fn = '{}.{}.metadata'.format(args.species, args.edge_type)
    bucket_dir = os.path.join(cls, args.species, args.edge_type)
    sync_dir = os.path.join(args.bucket, bucket_dir)
    sync_edges = os.path.join(sync_dir, edges_fn)
    sync_nodes = os.path.join(sync_dir, nodes_fn)
    sync_meta = os.path.join(sync_dir, meta_fn)

    if not args.force_fetch and all(map(os.path.exists, [sync_edges, sync_nodes, sync_meta])):
        print("Files already exist.  Skipping.")
        return

    get = get_gg if cls == 'Gene' else get_pg
    res = get(db, args.edge_type, args.species)

    print("ProductionLines: " + str(len(res)))
    if not args.force_fetch and should_skip(cls, res):
        print('Skipping {}.{}'.format(args.species, args.edge_type))
        return
    res, lines = norm_edges(res, args)

    n1des = list(set(i[0] for i in res))
    n2des = list(set(i[1] for i in res))

    n1des_desc = convert_nodes(args, n1des)
    n2des_desc = convert_nodes(args, n2des)
    nodes_desc = set(n1des_desc) | set(n2des_desc)

    metadata = get_metadata(db, res, nodes_desc, lines, args.species, args.edge_type, args)
    db.close()

    os.makedirs(sync_dir, exist_ok=True)
    with open(sync_edges, 'w') as file:
        csvw = csv.writer(file, delimiter='\t')
        csvw.writerows(res)
    with open(sync_nodes, 'w', encoding='utf-8') as file:
        csvw = csv.writer(file, delimiter='\t')
        csvw.writerows(nodes_desc)
    with open(sync_meta, 'w') as file:
        yaml.dump(metadata, file, default_flow_style=False)

if __name__ == "__main__":
    main()
