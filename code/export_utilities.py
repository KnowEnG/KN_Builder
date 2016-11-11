from argparse import ArgumentParser
import config_utilities as cf
import redis_utilities as ru
import mysql_utilities as mu
import sanitize_utilities as su
import csv, json
import os

def get_gg(db, et, taxon = 9606):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n1 ON s.n1_id = n1.node_id JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n1.taxon = {} AND n2.taxon = {} AND s.status = 'production';".format(et, taxon, taxon))

def get_pg(db, et, taxon = 9606):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n2.taxon = {} AND s.status = 'production';".format(et, taxon))


def figure_out_class(db, et):
    return db.run("SELECT n1_type, bidir FROM edge_type WHERE et_name = '{}'".format(et))[0]

def norm_edges(edges, args): #TODO: only do certain things if asked by options.
    if args.make_unweighted:
        edges = su.make_network_unwieghted(edges, 2)
    if args.make_undirected:
        edges = su.make_network_undirected(edges)
    edges = su.sort_network(edges)
    edges = su.drop_duplicates_by_type_or_node(edges)
    edges = su.normalize_network_by_type(edges, 3, 2)
    return edges

def get_nodes(edges):
    ret = set()
    for i in edges:
        ret.add(i[0])
        ret.add(i[1])
    return ret

def convert_genes(args, nodes):
    rdb = ru.get_database(args)
    return [ru.conv_gene(rdb, item, '', args.species) for item in nodes]
    return db.run("SELECT node_id, n_alias FROM node WHERE node_id IN ('{}')".format("','".join(nodes)))

def get_sources(edges):
    return set(edge[4] for edge in edges)

def get_metadata(db, sources, edges, nodes):
    return {"number_of_edges": len(edges),
            "number_of_nodes": len(nodes),
            "sources": [db.run("SELECT file_id, remote_url, remote_date, remote_version, checksum FROM raw_file WHERE file_id = '{}'".format(source))[0] for source in sources]}

def main():
    """
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    parser = su.add_config_args(parser)
    parser.add_argument("-e", "--edge_type", help="Edge type")
    parser.add_argument("-s", "--species", help="Species")
    args = parser.parse_args()

    db = mu.get_database(args = args)
    db.use_db("KnowNet")

    cls, bidir = figure_out_class(db, args.edge_type)
    edges_fn = '{}.{}.edge'.format(args.species, args.edge_type)
    nodes_fn = '{}.{}.node_map'.format(args.species, args.edge_type)
    meta_fn = '{}.{}.metadata'.format(args.species, args.edge_type)
    bucket_dir = os.path.join(cls, args.species, args.edge_type)
    sync_dir = os.path.join(args.working_dir, args.bucket, bucket_dir)
    sync_edges = os.path.join(sync_dir, edges_fn)
    sync_nodes = os.path.join(sync_dir, nodes_fn)
    sync_meta = os.path.join(sync_dir, meta_fn)

    if not args.force_fetch: #TODO: Check locally for files already existing.
        pass

    get = get_gg if cls == 'Gene' else get_pg
    res = get(db, args.edge_type)
    res = norm_edges(res, args)

    nodes = get_nodes(res)
    nodes_desc = convert_genes(args, nodes)

    sources = get_sources(res)
    metadata = get_metadata(db, sources, res, nodes_desc)
    db.close()

    os.makedirs(sync_dir, exist_ok=True)
    with open(sync_edges, 'w') as f:
        csvr = csv.writer(f, delimiter='\t')
        csvr.writerows(res)
    with open(sync_nodes, 'w') as f:
        csvr = csv.writer(f, delimiter='\t')
        csvr.writerows(nodes_desc)
    with open(sync_meta, 'w') as f:
        json.dump(metadata, f)

if __name__ == "__main__":
    main()
