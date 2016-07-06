USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:node_meta.csv" AS row FIELDTERMINATOR '\t'
MATCH (n:row.node_desc {node_id: row.node_id})
SET n.row.info_type = n.row.info_desc;

USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:edge_meta.csv" AS row FIELDTERMINATOR '\t'
MATCH (n1:row.n1_desc {node_id: row.n1_id})
MATCH (n2:row.n2_desc {node_id: row.n2_id})
MATCH (n1)-[r:row.et_name]->(n2)
SET r.row.info_type = r.row.info_desc;