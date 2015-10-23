"""
This script reads in a gctx file (from LINCS) and converts the genes to
ensembl identifiers
"""

import cmap.io.gct as gct
import cmap.util.api_utils as apiu
import re
import csv
import json
import sys
import subprocess
import time
import redis
import os

def conv_gene(rdb, foreign_key, hint, taxid):
    """Uses the redis database to convert a gene to enesmbl stable id

    This checks first if there is a unique name for the provided foreign key.
    If not it uses the hint and taxid to try and filter the foreign key
    possiblities to find a matching stable id.

    Args:
        rdb (redis object): redis connection to the mapping db
        foreign_key (str): the foreign gene identifer to be translated
        hint (str): a hint for conversion
        taxid (str): the species taxid
    """
    hint = hint.upper()
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
        if taxid == taxid_hint[0] and hint in taxid_hint[1]:
            both_match.append(taxid_hint_key)
        if taxid == taxid_hint[0]:
            taxid_match.append(taxid_hint_key)
        if hint in taxid_hint[1]:
            hint_match.append(taxid_hint_key)
    if both_match:
        both_ens_ids = list(set(rdb.mget(both_match)))
        if len(both_ens_ids) == 1:
            return both_ens_ids[0].decode()
    if taxid_match:
        taxid_ens_ids = list(set(rdb.mget(taxid_match)))
        if len(taxid_ens_ids) == 1:
            return taxid_ens_ids[0].decode()
    if hint_match:
        hint_ens_ids = list(set(rdb.mget(hint_match)))
        if len(taxid_ens_ids) == 1:
            return hint_ens_ids[0].decode()
    return 'unmapped-many'

if __name__ == '__main__':
    #read args
    try:
        gctx_file = sys.argv[1]
        tab_file = sys.argv[2]
        redis_host = sys.argv[3]
        redis_port = sys.argv[4]
    except:
        print("Usage:\npython affy2ens.py gctx_file "
                "lincs.baseline_gene_expression.txt redis_host redis_port")
        sys.exit()

    #static file paths
    gmap_file = os.path.join(os.path.dirname(tab_file), 'symbol2gene.txt')
    gmap_dict = os.path.join(os.path.dirname(tab_file), 'probe2symbol.json')
    probemap_file = os.path.join(os.path.dirname(tab_file), 'probe-map.txt')
    headers_file = os.path.join(os.path.dirname(tab_file), 'headers.json')

    #inits
    gmap = dict()
    grev = dict()
    emap = dict()
    erev = dict()
    head = dict()

    #connect to redis
    rdb = redis.StrictRedis(host=redis_host, port=redis_port)

    #get gene probes from the matrix
    GCTObject = gct.GCT(gctx_file)
    GCTObject.read(col_inds=range(0, 1))
    gene_probes = GCTObject.get_row_meta('id')

    #get the column index --> gene probe mapping dictionary
    for i in range(0, len(gene_probes)):
        head[i] = gene_probes[i]
    with open(headers_file, 'w') as outfile:
        json.dump(head, outfile, indent=4, sort_keys=True)

    #get the gmap_file
    os.system('cut -f1,3 ' + tab_file + ' | sort -u > ' + gmap_file)

    #get the gene probe --> gene symbol mapping dictionary
    if not os.path.isfile(gmap_dict):
        with open(gmap_file) as infile:
            for line in infile:
                line = str(line.strip()).split('\t')
                probe = line[0]
                symbol = line[1]
                if probe not in gmap:
                    gmap[probe] = symbol
                elif gmap[probe] != symbol:
                    gmap[probe] = gmap[probe] + '::' + symbol
        with open(gmap_dict, 'w') as outfile:
            json.dump(gmap, outfile, indent=4)
    else:
        with open(gmap_dict) as infile:
            gmap = json.load(infile)

    #produce the gene symbol --> gene probe mapping dictionary
    for pr_id in gmap:
        symbol = gmap[pr_id]
        grev[symbol] = grev.get(symbol, list())
        grev[symbol].append(pr_id)

    #produce the gene symbol --> ensembl id mapping dictionary
    count = 0
    for symbol in grev:
        count += 1
        sys.stdout.write('\rMapping: '+str(count))
        sys.stdout.flush()
        if symbol == u'NA':
            emap[symbol] = u'NA'
        else:
            emap[symbol] = conv_gene(rdb, symbol, '', '9606')

    #produce the ensembl id --> gene symbol mapping dictionary
    for symbol in emap:
        ens = emap[symbol]
        if 'unmapped' in ens:
            erev[ens] = [ens]
        else:
            erev[ens] = erev.get(ens, list())
            erev[ens].append(symbol)

    with open(probemap_file, 'w') as out:
        writer = csv.writer(out, delimiter = '\t')
        writer.writerow(['probe_id', 'gene_symbol', 'ens_gene', 'category',
                        'synonyms'])
        map_dict = dict()
        for pr_id in gene_probes:
            map_dict[pr_id] = list()
            symbol = gmap[pr_id]
            lincs_probes = grev[symbol]
            ens_id = emap[symbol]
            ens_symbols = erev[ens_id]
            probes = lincs_probes
            if len(ens_symbols) > 1:
                for sym in ens_symbols:
                    probes += grev[sym]
                probes = sorted(set(probes))

            line = [pr_id] #probe id
            line.append(symbol) #gene symbol
            line.append(ens_id) #ens gene
            map_dict[pr_id].append(ens_id)

            #if LINCS API did not have a mapping for the gene
            if symbol == u'NA':
                line.append('unknown:no-symbol') #category
                line.append(pr_id) #synonyms
                map_dict[pr_id].append(pr_id)
                map_dict[pr_id].append([gene_probes.index(pr_id)])
                writer.writerow(line)
                continue

            #if LINCS API did have a mapping for the gene
            #if ensembl didn't have a mapping for the gene symbol
            if 'unmapped' in ens_id:
                line.append('unknown:no-ensembl') #category
            #if both LINCS and ensembl mapped uniquely
            elif len(lincs_probes) == 1 and len(ens_symbols) == 1:
                line.append('unique') #category
            elif len(lincs_probes) > 1 and len(ens_symbols) == 1:
                line.append('many-to-one:symbol') #category
            elif len(lincs_probes) == 1 and len(ens_symbols) > 1:
                line.append('many-to-one:ensembl') #category
            else:
                line.append('many-to-one:symbol&ensembl') #category
            line.append(','.join(probes)) #synonyms
            map_dict[pr_id].append(probes)
            indices = list()
            for pr in probes:
                indices.append(gene_probes.index(pr))
            map_dict[pr_id].append(indices)
            writer.writerow(line)

    #clean up
    with open(os.path.splitext(tab_file)[0] + '.json', 'w') as outfile:
        json.dump(map_dict, outfile, sort_keys=True, indent=4)
    os.remove(gmap_file)
    os.remove(gmap_dict)

    print('\nDone.')