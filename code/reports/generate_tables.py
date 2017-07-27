from csv import reader, writer, DictReader
from sys import stdout
from collections import defaultdict
from glob import glob
from yaml import load
from pprint import pprint

def fold(l):
    ret = defaultdict(lambda: [])
    for e in l:
        if e[1] == 'ALL':
            ret[e[0]].extend(e[2:])
        else:
            ret[e[0]][:0] = e[2:]
    return [[k] + v for k, v in ret.items()]

r = reader(open("subnetwork_summaries.txt"), delimiter=' ')

species = []
gene_gene = []
gene_prop = []
gene_edge_type = []
prop_edge_type = []
contents = [("Version:", "KN-20rep-1706"), ["Number of Species:", 0], ("Number of Resources:", 14)]

for line in r:
    if all(map(lambda x: x == "ALL", line[0:3])):
        species.append([line[3], int(line[8])/1_000_000, int(line[7])/1_000, int(line[6])/1_000, int(line[9])])
        if line[3] == "ALL":
            contents.append(("Number of Datasets:", line[9]))
            contents.append(("Number of Edge Types:", line[4]))
            contents.append(("Number of Edges:", line[8]))
            contents.append(("Number of Nodes:", line[5]))
            contents.append(("Number of Gene Nodes:", line[6]))
            contents.append(("Number of Property Nodes:", line[7]))
        else:
            contents[1][1] += 1
    if line[0] == "Gene" and line[2] == "ALL" and line[3] in ["ALL", "9606"]:
        gene_gene.append([line[1], line[3], int(line[8])/1_000_000, int(line[9])])
    if line[0] == "Property" and line[2] == "ALL" and line[3] in ["ALL", "9606"]:
        gene_prop.append([line[1], line[3], int(line[8])/1_000_000, int(line[7])/1_000, int(line[9])])
    if line[0] == "Gene" and line[2] != "ALL" and line[3] in ["ALL", "9606"]:
        gene_edge_type.append([line[2], line[3], int(line[8])/1_000_000, int(line[6])/1_000, int(line[9])])
    if line[0] == "Property" and line[2] != "ALL" and line[3] in ["ALL", "9606"]:
        prop_edge_type.append([line[2], line[3], int(line[8])/1_000_000, int(line[7])/1_000, int(line[6])/1_000, int(line[9])])

w = writer(open("contents_table.csv", 'w'))
w.writerows(contents)

w = writer(open("species_table.csv", 'w'))
w.writerow(["Species", "Network Edges (millions)", "Property Nodes (thousands)", "Gene Nodes (thousands)", "Datasets"])
w.writerows(sorted(species, key=lambda x: x[1], reverse=True))

w = writer(open("GGrels_table.csv", 'w'))
w.writerow(["Edge Type Collection", "Human Only<br>Network Edges (millions)", "Datasets", "All Species<br>Network Edges (millions)", "Datasets"])
w.writerows(sorted(fold(gene_gene), key=lambda x: x[1], reverse=True))

w = writer(open("PGrels_table.csv", 'w'))
w.writerow(["Edge Type Collection", "Human Only<br>Network Edges (millions)", "Property Nodes (thousands)", "Datasets", "All Species<br>Network Edges (millions)", "Property Nodes (thousands)", "Datasets"])
w.writerows(sorted(fold(gene_prop), key=lambda x: x[1], reverse=True))

w = writer(open("GGtypes_table.csv", 'w'))
w.writerow(["Edge Type Collection", "Human Only<br>Network Edges (millions)", "Gene Nodes (thousands)", "Datasets", "All Species<br>Network Edges (millions)", "Gene Nodes (thousands)", "Datasets"])
w.writerows(sorted(fold(gene_edge_type), key=lambda x: x[1], reverse=True))

w = writer(open("PGtypes_table.csv", 'w'))
w.writerow(["Edge Type Collection", "Human Only<br>Network Edges (millions)", "Property Nodes (thousands)", "Gene Nodes (thousands)", "Datasets", "All Species<br>Network Edges (millions)", "Property Nodes (thousands)", "Gene Nodes (thousands)", "Datasets"])
w.writerows(sorted(fold(prop_edge_type), key=lambda x: x[1], reverse=True))

r = DictReader(open("source_summaries.txt"), delimiter='\t')
src_sums = {(e["type"], e["source"]): e for e in r}

temp_srcs = {e["resource"]: e for e in DictReader(open("/home/aidane/Downloads/test.csv"))}

def compress(d, v):
    d = [e[v] for e in d]
    if all(map(lambda x: isinstance(x, list), d)):
        d = sum(d, [])
    return set(d)

d = defaultdict(lambda: {})
for f in glob('KN-20rep-1706/userKN-20rep-1706/**/*.metadata', recursive=True):
    with open(f) as metadata:
        data = load(metadata)
        for k, v in data['datasets'].items():
            source, alias = k.split('.', 1)
            if source in d and alias in d[source] and "edge_type" in d[source][alias]:
                temp = d[source][alias]["edge_type"] 
            else:
                temp = []
            d[source][alias] = v
            d[source][alias]["edge_type"] = temp + [data['edge_type']['id']]
d2 = defaultdict(lambda: {})
for k, v in d.items():
    d2[k]["keys"] = [k + '.' + e for e in v.keys()]
    d2[k]["len"] = len(v)
    for i in ["pmid", "license", "name", "description"]:
        d2[k][i] = temp_srcs[k][i]
    for i in ["image", "reference", "source_url"]:
        temp = compress(v.values(), i)
        if len(temp) > 1:
            raise ValueError(f"Too many different values for {i}: {temp}")
        else:
            temp = temp.pop()
        d2[k][i] = temp
    for i in ["download_url", "edge_type"]:
        d2[k][i] = compress(v.values(), i)
    d2[k]["nodes"] = src_sums["*/chunks/*.unique.node.*", k]["lines"]
    d2[k]["edges"] = src_sums["*/chunks/*.unique.edge.*", k]["lines"]

w = writer(open("KNDR_sum_table.csv", 'w'))
for k, l in d2.items():
    w.writerow([f'<img src="{l["image"]}">', f'<a href="{l["source_url"]}">{l["name"]}</a>{": " + l["description"] if l["description"] else ""}', f'Nodes: {l["nodes"]}, Edges: {l["edges"]}'])

w = writer(open("KNDR_full_table.csv", 'w'))
w.writerow(["Resource", "Reference", "Source Files", "License"])
for k, l in d2.items():
    w.writerow([l['name'], f'{l["reference"]} <a href="https://www.ncbi.nlm.nih.gov/pubmed/{l["pmid"]}">Pudmed</a>', '<br>'.join(l["download_url"]), l["license"]])
