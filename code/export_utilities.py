from argparse import ArgumentParser
import config_utilities as cf
import mysql_utilities as mu
import csv
import boto3
import io

def get_gg(db, et, taxon = 9606):
    return db.run("SELECT s.edge_hash, s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n1 ON s.n1_id = n1.node_id JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n1.taxon = {} AND n2.taxon = {} AND s.status = 'production';".format(et, taxon, taxon))

def get_pg(db, et, taxon = 9606):
    return db.run("SELECT s.edge_hash, s.n1_id, s.n2_id, s.weight, s.et_name, rl.file_id, rl.line_num FROM status s JOIN node_species n2 ON s.n2_id = n2.node_id JOIN raw_line rl ON s.line_hash = rl.line_hash WHERE s.et_name = '{}' AND n2.taxon = {} AND s.status = 'production';".format(et, taxon))


def main():
    """
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    db = mu.get_database(args = args)
    db.use_db("KnowNet")
    res = get_pg(db, 'pfam_domains')
    with open("/tmp/temp.txt", 'w') as f: # How to get a temp file?
        csvr = csv.writer(f)
        csvr.writerows(res)
    s3 = boto3.resource('s3')
    s3.Object('aepstei3', 'test.csv').upload_file('/tmp/temp.txt')

if __name__ == "__main__":
    main()
