from argparse import ArgumentParser
import config_utilities as cf
import redis_utilities as ru
import mysql_utilities as mu
import sanitize_utilities as su
import csv, yaml
import os
from datetime import datetime

def get_gg(db, et, taxon):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n1 ON s.n1_id = n1.node_id JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n1.taxon = {} AND n2.taxon = {} AND s.status = 'production';".format(et, taxon, taxon))

def get_pg(db, et, taxon):
    return db.run("SELECT s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n2.taxon = {} AND s.status = 'production';".format(et, taxon))


def figure_out_class(db, et):
    return db.run("SELECT n1_type, bidir FROM edge_type WHERE et_name = '{}'".format(et))[0]

def norm_edges(edges, args):
    if args.make_unweighted:
        edges = su.make_network_unweighted(edges, 2)
        print("UnweightedLines: " + str(len(edges)))
    if args.make_undirected: #TODO: less important, yes, no, auto
        edges = su.make_network_undirected(edges)
        print("UndirectedLines: " + str(len(edges)))
    edges = su.sort_network(edges)
    print("SortedLines: " + str(len(edges)))
    edges = su.drop_duplicates_by_type_or_node(edges, 0, 1, 3)
    print("DeDuplicatedEdges: " + str(len(edges)))
    if args.make_undirected: #TODO: less important, yes, no, auto
        edges = su.upper_triangle(edges, 0, 1)
        print("UpperTriangleEdges: " + str(len(edges)))
    edges = su.normalize_network_by_type(edges, 3, 2) #TODO: none, all, type
    print("NormalizedEdges: " + str(len(edges)))
    return edges

def convert_nodes(args, nodes):
    rdb = ru.get_database(args)
    return ru.get_node_info(rdb, nodes, None, None, args.species)

def get_sources(edges):
    return set(edge[4] for edge in edges)

def get_metadata(db, edges, nodes, sp, et):
    sources = get_sources(edges)
    datasets = {}
    for source in sources:
        file_id, remote_url, remote_date, remote_version, source_url, image, reference, date_downloaded, checksum = \
                db.run("SELECT file_id, remote_url, remote_date, remote_version, source_url, image, reference, " \
                       "date_downloaded, checksum FROM raw_file WHERE file_id = '{}'".format(source))[0]
        datasets[file_id] = {"source_url": source_url, "image": image, "reference": reference, "download_url": remote_url, "remote_version": remote_version, "remote_date": datetime.utcfromtimestamp(float(remote_date)), "download_date": date_downloaded, "file_checksum": checksum}

    sciname, = db.run("SELECT sp_sciname FROM species WHERE taxon = '{}'".format(sp))[0]
    n1_type, n2_type, bidir, et_desc, sc_desc, sc_best, sc_worst = db.run("SELECT n1_type, n2_type, bidir, et_desc, sc_desc, sc_best, sc_worst FROM edge_type WHERE et_name = '{}'".format(et))[0]


    num_prop, num_gene, num_none = 0, 0, 0
    for _, _, type, _, _ in nodes:
        if type == "Property":
            num_prop += 1
        elif type == "Gene":
            num_gene += 1
        elif type == "None":
            num_none += 1
        else:
            raise ValueError("Invalid type: {}".format(type))

    return {"id": ".".join([sp, et]),
            "species": {"taxon_identifer": sp, "scientific_name": sciname},
            "edge_type": {"id": et, "n1_type": n1_type, "n2_type": n2_type, "type_desc": et_desc, "score_desc": sc_desc, "score_best": sc_best, "score_worst": sc_worst},
            "datasets": datasets,
            "data": {"num_edges": len(edges), "num_nodes": len(nodes), "num_prop_nodes": num_prop, "num_gene_nodes": num_gene}}
            #"build_metadata": {"git_revision": , "date": , "command": }}

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
    res = get(db, args.edge_type, args.species)
    print("ProductionLines: " + str(len(res)))
    if cls == 'Property':
        # TODO: remove small properties
        pass
    res = norm_edges(res, args)

    n1des = list(set(i[0] for i in res))
    n2des = list(set(i[1] for i in res))
    
    n1des_desc = convert_nodes(args, n1des)
    n2des_desc = convert_nodes(args, n2des)
    nodes_desc = set(n1des_desc) | set(n2des_desc)

    metadata = get_metadata(db, res, nodes_desc, args.species, args.edge_type)
    db.close()

    os.makedirs(sync_dir, exist_ok=True)
    with open(sync_edges, 'w') as f:
        csvw = csv.writer(f, delimiter='\t')
        csvw.writerows(res)
    with open(sync_nodes, 'w') as f:
        csvw = csv.writer(f, delimiter='\t')
        csvw.writerows(nodes_desc)
    with open(sync_meta, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

if __name__ == "__main__":
    main()
