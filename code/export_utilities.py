from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as mu
import csv, json
import boto3, botocore
import os

def get_gg(db, et, taxon = 9606):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n1 ON s.n1_id = n1.node_id JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n1.taxon = {} AND n2.taxon = {} AND s.status = 'production';".format(et, taxon, taxon))

def get_pg(db, et, taxon = 9606):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n2.taxon = {} AND s.status = 'production';".format(et, taxon))


def figure_out_class(db, et):
    return db.run("SELECT n1_type, bidir FROM edge_type WHERE et_name = '{}'".format(et))[0]

def norm_edges(edges):
    return edges

def get_nodes(edges):
    ret = set()
    for i in edges:
        ret.add(i[0])
        ret.add(i[1])
    return ret

def convert_genes(db, nodes):
    return db.run("SELECT node_id, n_alias FROM node WHERE node_id IN ('{}')".format("','".join(nodes)))

def get_sources(edges):
    return list(set(edge[4] for edge in edges))

def get_metadata(db, sources):
    return {"sources": sources}

def main():
    """
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    parser.add_argument("-b", "--bucket_name", help="Name of the S3 bucket")
    parser.add_argument("-e", "--edge_type", help="Edge type")
    parser.add_argument("-s", "--species", help="Species")
    args = parser.parse_args()

    db = mu.get_database(args = args)
    db.use_db("KnowNet")

    cls, bidir = figure_out_class(db, args.edge_type)
    edges_fn = 'network.edges'
    nodes_fn = 'nodes.meta'
    meta_fn = 'sources.meta'
    bucket_dir = os.path.join(cls, args.species, args.edge_type)
    sync_dir = os.path.join(args.working_dir, args.bucket_name, bucket_dir)
    sync_edges = os.path.join(sync_dir, edges_fn)
    sync_nodes = os.path.join(sync_dir, nodes_fn)
    sync_meta = os.path.join(sync_dir, meta_fn)
    bucket_edges = os.path.join(bucket_dir, edges_fn)
    bucket_nodes = os.path.join(bucket_dir, nodes_fn)
    bucket_meta = os.path.join(bucket_dir, meta_fn)

    s3 = boto3.resource('s3')
    s3edges = s3.Object(args.bucket_name, bucket_edges)
    s3nodes = s3.Object(args.bucket_name, bucket_nodes)
    s3meta = s3.Object(args.bucket_name, bucket_meta)

    if not args.force_fetch:
        try:
            if s3edges.content_length > 0 and s3nodes.content_length > 0 and s3meta.content_length > 0:
                return
        except botocore.exceptions.ClientError as e: #Maybe check to make sure the error is not found?
            pass

    get = get_gg if cls == 'Gene' else get_pg
    res = get(db, args.edge_type)
    res = norm_edges(res)

    nodes = get_nodes(res)
    nodes_desc = convert_genes(db, nodes)

    sources = get_sources(res)
    metadata = get_metadata(db, sources)
    db.close()


    os.makedirs(sync_dir, exist_ok=True)
    with open(sync_edges, 'w') as f:
        csvr = csv.writer(f)
        csvr.writerows(res)
    with open(sync_nodes, 'w') as f:
        csvr = csv.writer(f)
        csvr.writerows(nodes_desc)
    with open(sync_meta, 'w') as f:
        json.dump(metadata, f)

    s3edges.upload_file(sync_edges)
    s3nodes.upload_file(sync_nodes)
    s3meta.upload_file(sync_meta)

if __name__ == "__main__":
    main()
