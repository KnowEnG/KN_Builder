"""
KnowEnG API for effectively fetching information from MySQL database of Project 1
Contains API method call:
    list_edge_types()
    list_edges()
    edge_meta()
    edge_summary()
    list_nodes()
    id_conversion()
    gene_summary()
"""

from flask import Flask, jsonify,request
import pymysql
from collections import Counter

db = pymysql.connect(host="knowdevs.dyndns.org",    # your host, usually localhost
                     user="root",         # your username
                     passwd="KnowEnG",  # your password
                     port=3399,
                     db="KnowNet")        # name of the data base
cur = db.cursor()

cur.execute("SELECT * FROM edge_type")
edge_types = cur.fetchall()

"""Join edge_types, status, edge_meta, node_species into a new edge_merge
   Each edge contains parameters such as n1_id, n2_id, et_name, n1_type_id, n2_type_id, n1_taxon, n2_taxon
"""
cur.execute("SELECT DISTINCT s.n1_id, s.n2_id, s.et_name, s.weight, s.edge_hash, n1.n1_type_id, n2.n2_type_id, n1.n1_taxon, n2.n2_taxon \
             FROM status s \
             left join (SELECT node.node_id AS n1_id, node.n_type_id as n1_type_id, node_species.taxon as \
             n1_taxon FROM node LEFT JOIN node_species ON node.node_id = node_species.node_id) n1 ON s.n1_id = n1.n1_id \
             left join (SELECT node.node_id AS n2_id, node.n_type_id as n2_type_id, node_species.taxon as \
             n2_taxon FROM node LEFT JOIN node_species ON node.node_id = node_species.node_id) n2 ON s.n2_id = n2.n2_id")
edges = cur.fetchall()

"""Join node, node_meta, node_species into a new node_merge table
    Each node contains parameters such as node_id, n_alias, n_type_id, info_type, info_desc, taxon
"""
cur.execute("SELECT DISTINCT node.node_id, n_alias, n_type_id, info_type, info_desc, taxon FROM node \
             LEFT JOIN node_species ON node.node_id = node_species.node_id \
             LEFT JOIN node_meta ON node.node_id = node_meta.node_id; ")
nodes = cur.fetchall()
print(len(edges), len(nodes))



app = Flask(__name__)
@app.route("/v1")
def hello():
    return "KnowNet_P1_Api_v1.0"



@app.route("/v1/edges/edge_types",methods=['GET'])
def list_edge_types():
    """Show all or partial edge types based on connected nodes' type.
    
    If one wants to show all the edge types, queried by /v1/edges/edge_types.
    Otherwise, specify the node type of n1 and n2 in no partial order. Node type
    could be either 1(Gene), 2(Property) or 3(Molecule)
    Args:
        n1_type(str): the type of the first node
        n2_type(str): the type of the second node
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/edges/edge_types?n1_type=1&n2_type=3
    """
    n1_type, n2_type = request.args.get('n1_type'), request.args.get('n2_type')
    if not n1_type and not n2_type:
        return jsonify({'edge_types':[{"et_names": et[0],\
                                 "n1_types": et[1],\
                                 "n2_types": et[2],\
                                 "bidir": et[3],\
                                 "et_desc": et[4],\
                                 "sc_desc": et[5],\
                                 "sc_range": [et[7],et[6]]
                        } for et in edge_types]})
    elif not n1_type or not n2_type:
        return "Miss Parameters."
    else:
        selected_et = [et for et in edge_types if ((str(et[1]) == n1_type and str(et[2]) == n2_type) or (str(et[2]) == n1_type and str(et[1]) == n2_type))]
        return jsonify({'edge_types':[{"et_names": et[0],\
                                 "n1_types": et[1],\
                                 "n2_types": et[2],\
                                 "bidir": et[3],\
                                 "et_desc": et[4],\
                                 "sc_desc": et[5],\
                                 "sc_range": [et[7],et[6]]
                        } for et in selected_et]})

@app.route("/v1/edges",methods=["GET"])
def list_edges():
    """Show all edges in a subnetwork constrained by edge_types, nodes and species
    
    Construct a subnetwork constrained by edge_types, nodes and species and return
    all edges inside the subnetwork.
    Args:
        et(str): the edge type of edges in the subnetwork, separated by colon. 'ALL' if no constrains on edge_types
        nodes(str): nodes contained in the subnetwork, separated by colon. 'ALL' if no constrains on nodes
        species(str): the species of nodes in the subnetwork, separated by colon. 'ALL' if no constrains on specices
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/edges?et=pathcom_pathway&nodes=ALL&species=ALL
    """
    et,nodes,species = request.args.get('et'), request.args.get('nodes'), request.args.get('species')
    if not et and not nodes and not species:
        return "Size of edges: " + str(len(edges))
    if not et or not nodes or not species:
        return "Miss Parameters."
    edge_set = []
    if et == "ALL":
        edge_set = edges
    else:
        et = et.split(":")
        edge_set = [e for e in edges if e[2] in et]
    if not nodes == "ALL":
        nodes = nodes.split(":")
        edge_set = [e for e in edge_set if e[0] in nodes and e[1] in nodes]
    if not species == "ALL":
        species = species.split(":")
        edge_set = [e for e in edge_set if str(e[7]) in species and str(e[8]) in species]
    edge_set = map(list, edge_set)
    return jsonify({'edges':[{"n1_id": e[0],\
                              "n2_id": e[1],\
                              "et_name": e[2],\
                              "weight": e[3],\
                    } for e in edge_set]})

@app.route("/v1/edges/meta",methods=["GET"])
def edge_meta()

@app.route("/v1/edges/summary",methods=["GET"])
def edge_summary():
    """Produced summary for a subnetwork constrained by edge_types, nodes and species
    
    Based on the subnetwork produced, study the number or nodes, number of edges, highest degree and lowest degree \
    in the subnetwork as well as the size of the adjacent nodes.
    Args:
        et(str): the edge type of edges in the subnetwork, separated by colon. 'ALL' if no constrains on edge_types
        nodes(str): nodes contained in the subnetwork, separated by colon. 'ALL' if no constrains on nodes
        species(str): the species of nodes in the subnetwork, separated by colon. 'ALL' if no constrains on specices
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/edges/summary?et=ALL&nodes=paco_AR_protein_affects_the_reaction__Dihydrotestosterone_resul:paco_BMS453_inhibits_the_reaction__Tretinoin_inhibits_the_react:ENSG00000140009&species=ALL
    """
    et,nodes,species = request.args.get('et'), request.args.get('nodes'), request.args.get('species')
    if not et and not nodes and not species:
        return "Size of edges: " + str(len(edges))
    if not et or not nodes or not species:
        return "Miss parameters."
    edge_set = []
    if et == "ALL":
        edge_set = edges
    else:
        et = et.split(":")
        edge_set = [e for e in edges if e[2] in et]
    if not nodes == "ALL":
        nodes = nodes.split(":")
        edge_set = [e for e in edge_set if e[0] in nodes and e[1] in nodes]
    if not species == "ALL":
        species = species.split(":")
        edge_set = [e for e in edge_set if e[7] in species and e[8] in species]
    edge_set = map(list, edge_set)
  
    node_list = Counter()
    for e in edge_set:
        nodes = Counter({e[0]:1, e[1]:1})
        node_list = node_list + nodes
    max_degree = node_list.most_common(1)[0][1]
    node_hub = [i for i,z in node_list.most_common() if z == max_degree]

    min_degree = node_list.most_common()[-1][1]
    node_border = [i for i,z in node_list.most_common() if z == min_degree]
  
    ##Include all adjacent nodes of the subgraph
    e_ex = [e1 for e1 in edges for e2 in edge_set if e1[4] != e2[4]]
    adjacent_nodes = [e1[0] for e1 in e_ex if e1[0] not in node_list.keys()]
    adjacent_nodes.extend([e1[1] for e1 in e_ex if e1[1] not in node_list.keys()])
    adjacent_nodes = list(set(adjacent_nodes))
    return jsonify({'highest_degree': {"degree":max_degree, "nodes": node_hub}, \
                  "lowest_degree": {"degree":min_degree,  "nodes": node_border}, \
                  "adjacent_nodes": len(adjacent_nodes), \
                  "node_count": len(node_list), \
                    "edge_count": len(edge_set)})

@app.route("/v1/nodes", methods=["GET"])
def list_nodes():
    """List selected nodes and their detailed informations

    Args:
        node_id(str): the id for the chosen nodes, separated by colon
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/nodes?node_id=ENSG00000236802
    """
    node_id = request.args.get('node_id')
    if not node_id:
        return "Size of nodes: " + str(len(nodes))
    node_set = []
    if node_id == "ALL":
        node_set = nodes
    else:
        node_id = node_id.split(":")
        node_set = [n2 for n1 in node_id for n2 in nodes if n1 == n2[0]]
    node_set = map(list, node_set)
    for n in node_set:
        n[2] = "Gene" if n[2] == 1 else "Property" if n[2] == 2 else "Molecule" if n[2] == 3 else "Unknown_type"
        if not n[4]:
            n[4] = "N.A."
    return jsonify({"node":[{"node_id": n[0],
                          "node_type": n[2],
                          "node_desc": n[4]} for n in node_set]})



@app.route("/v1/nodes/identifier", methods=['GET'])
def id_conversion():
    """Return corresponding node identifiers of KnowEnG's node identifier

    Args:
        node_id(str): the id for the chosen nodes, separated by colon
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/nodes/identifier?node_id=AT1G01020:21S_rRNA
    """
    node_id = request.args.get('node_id')
    if not node_id:
        return "Please enter an existing node_id"
    node_id = node_id.split(":")
    n_map = {}
    for n in nodes:
        index_valeu = -1
        if n[1]:
            try:
                index_valeu = n[1].index("[")
            except ValueError:
                index_valeu = len(n[1])
            n_map[n[0]] = n[1][:index_valeu].split(":")
        else:
            n_map[n[0]] = "N.A."
    return jsonify({"Identifier":[{t:n_map[t] for t in node_id}]})
  
@app.route("/v1/nodes/summary", methods=["GET"])
def gene_summary():
    """Return the lowest and highest degree of a gene set, as well as the corresponding nodes
    
    Args:
        node_id(str): the id for the chosen nodes, separated by colon
    An example URI is:
        http://knowdevs.dyndns.org:8099/v1/nodes/summary?node_id=ENSG00000188157:ENSG00000276333:ENSG00000041357:ENSG00000100387
    """
    node_id = request.args.get('node_id')
    print("x")
    node_id = node_id.split(":")
    node_list = Counter()
    for e in edges:
        if e[0] in node_id:
            node_list[e[0]] += 1
        if e[1] in node_id:
            node_list[e[1]] += 1
    print("y")
    max_degree = node_list.most_common(1)[0][1]
    print("a")
    node_hub = [i for i,z in node_list.most_common() if z == max_degree]
    print("b")
    min_degree = node_list.most_common()[-1][1]
    print("c")
    node_border = [i for i,z in node_list.most_common() if z == min_degree]
    print("d")
    return jsonify({"max_degree": [max_degree, node_hub], \
                  "min_degree": [min_degree, node_border]})
if __name__ == "__main__":
    app.run(debug=True,port=8080)
