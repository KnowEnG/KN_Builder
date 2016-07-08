USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:/shared/neo4j.node_meta.txt" 
AS row FIELDTERMINATOR '\t'
MATCH (n:Property {node_id: row.node_id})
SET n.meta_type = row.info_type 
SET n.meta_data = row.info_desc
RETURN n;

USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:/shared/neo4j.edge_meta.txt" 
AS row FIELDTERMINATOR '\t'
MATCH (n1 {node_id: row.n1_id})
MATCH (n2 {node_id: row.n2_id})
MATCH (n1)-[r:row.et_name]->(n2)
SET r.row.info_type = r.row.info_desc;