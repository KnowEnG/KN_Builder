"""Utiliites for cleaning files of in the mitab format.

Classes:

Functions:
    2table(raw_line, version_dict) -> str: takes as input a fetched file in
        MITAB format and a dictionary object version_dict describing the file.
        Produces the 2table edge file, edge_meta file and node_meta files.

Variables:
"""

import json
import os
import csv
import re
import hashlib
import table_utilities as tu

def table(raw_line, version_dict, taxid_list=None):
    """Uses the provided raw_line file to produce a table file, an
    edge_meta file, a node and/or node_meta file (only for property nodes).

    This returns noting but produces the table formatted files from the
    provided raw_line file:
        raw_line (line_hash, line_num, file_id, raw_line)
        table_file (line_hash, n1name, n1hint, n1type, n1spec,
                    n2name, n2hint, n2type, n2spec, et_hint, score,
                    table_hash)
        edge_meta (line_hash, info_type, info_desc)
        node_meta (node_id,
                   info_type (evidence, relationship, experiment, or link),
                   info_desc (text))
        node (node_id, n_alias, n_type)

    Args:
        raw_line(str): The path to the raw_line file
        version_dict (dict): A dictionary describing the attributes of the
            alias for a source.
        taxid_list (list): A list of taxon ids to support

    Returns:
    """
    if taxid_list is None:
        taxid_list = []

    #outfiles
    table_file = raw_line.replace('raw_line', 'table')
    e_meta_file = raw_line.replace('raw_line', 'edge_meta')

    #static column values
    n1type = 'gene'
    n2type = 'gene'
    score = 1
    src_specific_hints = ["intact", "biogrid"]
    #mapping files
    ppi = os.path.join('..', '..', 'ppi', 'obo_map', 'ppi.obo_map.json')
    with open(ppi) as infile:
        term_map = json.load(infile)

    with open(raw_line, encoding='utf-8') as infile, \
        open(table_file, 'w') as edges,\
        open(e_meta_file, 'w') as e_meta:
        edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
        e_meta_writer = csv.writer(e_meta, delimiter='\t', lineterminator='\n')
        for line in infile:
            line = line.replace('"', '').strip().split('\t')
            if len(line) == 1:
                continue
            if line[1] == '1':
                continue
            chksm = line[0]
            raw = line[3:]
            n1list = raw[0].split('|') + raw[2].split('|')
            n2list = raw[1].split('|') + raw[3].split('|')
            if not n1list or not n2list:
                continue
            match = re.search(r'taxid:(\d+)', raw[9])
            if match is not None:
                n1spec = match.group(1)
                if taxid_list and n1spec not in taxid_list:
                    continue
            else:
                continue
            match = re.search(r'taxid:(\d+)', raw[10])
            if match is not None:
                n2spec = match.group(1)
                if taxid_list and n2spec not in taxid_list:
                    continue
            else:
                continue
            if len(raw) > 35 and raw[35].upper() == 'TRUE':
                et_hint = 'PPI_negative'
            else:
                match = re.search(r'(MI:\d+)', raw[11])
                if match is not None:
                    et_hint = term_map[match.group(1)]
                else:
                    continue
            for n1tuple in n1list:
                if n1tuple.count(':') != 1:
                    continue
                n1hint, n1id = n1tuple.split(':')
                if n1hint in src_specific_hints:
                    continue
                for n2tuple in n2list:
                    if n2tuple.count(':') != 1:
                        continue
                    n2hint, n2id = n2tuple.split(':')
                    if n2hint in src_specific_hints:
                        continue
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1id, n1hint, n1type, n1spec,\
                        n2id, n2hint, n2type, n2spec, et_hint, str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1id, n1hint, n1type, n1spec, \
                        n2id, n2hint, n2type, n2spec, et_hint, score, t_chksum])

            publist = raw[8]
            interaction_id = raw[13]
            e_meta_writer.writerow([chksm, 'reference', publist])
            e_meta_writer.writerow([chksm, 'detail', interaction_id])

    outfile = e_meta_file.replace('edge_meta', 'unique.edge_meta')
    tu.csu(e_meta_file, outfile)