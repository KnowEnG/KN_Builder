"""
This script reads in a gctx file (from LINCS) and converts to a tsv file
"""

import cmap.io.gct as gct
import cmap.util.api_utils as apiu
import re
import csv
import sys
import redis
from itertools import chain

gctx_file = sys.argv[1]
remote_version = sys.argv[2]
tsv_file = sys.argv[3]
match = re.search('([0-9]*)x([0-9]*)', remote_version)
ncols = int(match.group(1))
nrows = int(match.group(2))
chunk_sz = 2000

count = 0
with open(tsv_file, 'w') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    GCTObject = gct.GCT(gctx_file)
    GCTObject.read(col_inds=range(0, 1))

    #write the headers
    gene_probes = GCTObject.get_row_meta('id')
    gene_probes.insert(0, '')
    #genes = list()
    #genes.append('')
    #ac = apiu.APIContainer(key="073d5d50cc31dbfe76603bd524bb5011")
    #rdb = redis.StrictRedis(host='knowice.cs.illinois.edu', port='6381')
    #for pr_id in gene_probes:
    #    mapped = ac.geneinfo.find({'pr_id' : pr_id},
    #                        fields = ['pr_gene_symbol', 'pr_gene_id'])[0]
    #    entrez = str(mapped[u'pr_gene_id'])
    #    symbol = str(mapped[u'pr_gene_symbol'])
    #    if entrez == '-666' and symbol == '-666':
    #        gene = 'unknown:' + pr_id
    #        print(gene, 'entrez=' + entrez, 'symbol=' + symbol)
    #    elif entrez != '-666':
    #        gene = rdb.get('9606::ENTREZGENE::' + entrez)
    #        if gene is None or gene == 'unmapped-many'.encode():
    #            gene = rdb.get('unique::' + symbol)
    #            if gene is None or gene == 'unmapped-many'.encode():
    #                gene = 'unknown:' + pr_id
    #                print(gene, 'entrez=' + entrez, 'symbol=' + symbol)
    #    else:
    #        gene = rdb.get('unique::' + symbol)
    #        if gene is None or gene == 'unmapped-many'.encode():
    #            gene = 'unknown:' + pr_id
    #            print(gene, 'entrez=' + entrez, 'symbol=' + symbol)
    #    genes.append(gene)

    writer.writerow(gene_probes)
    #print('')

    for i in range(0, ncols/chunk_sz + 1):
        start = i*chunk_sz
        end = min(i*chunk_sz + chunk_sz, ncols)
        GCTObject = gct.GCT(gctx_file)
        GCTObject.read(col_inds=range(start, end))
        count = end
        sys.stdout.write('\r'+str(count) + '/' + str(ncols))
        sys.stdout.flush()
        GCTMatrix = GCTObject.matrix

        for j in range(0, GCTMatrix.shape[1]):
            #get the experiment (distil_id)
            distil_id = GCTObject.get_column_meta('id')[j]
            row = [round(elem, 4) for elem in GCTMatrix[:,j].tolist()]
            row.insert(0, distil_id)
            #write row
            writer.writerow(row)
        sys.stdout.write('\rWritten to file')
        sys.stdout.flush()

sys.stdout.write('\r'+str(count) + '/' + str(ncols) + ' writen.      \nDone.\n')
sys.stdout.flush()


