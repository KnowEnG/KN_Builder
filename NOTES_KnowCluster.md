# Full Pipeline Run
### (on knowcluster01 in /workspace/knowtmp/project1/)

## Set environment variables
```
KNP_CHRONOS_URL='knowcluster01.dyndns.org:4400'
KNP_WORKING_DIR='/workspace/knowtmp/project1'
KNP_STORAGE_DIR='/mnt/knowstorage/project1'
KNP_DATA_PATH='data_6sp'
KNP_LOGS_PATH='logs_6sp'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MARATHON_URL='knowcluster01.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knowcluster05.dyndns.org'
KNP_MYSQL_PORT='3307'
KNP_MYSQL_DIR='/mnt/knowtmp/project1/p1_mysql-3307'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='10000'
KNP_MYSQL_CPU='2.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL='knowcluster05.dyndns.org'

KNP_REDIS_HOST='knowcluster07.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_REDIS_DIR='/mnt/knowtmp/project1/p1_redis-6380'
KNP_REDIS_MEM='8000'
KNP_REDIS_CPU='2.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL='knowcluster07.dyndns.org'

KNP_NGINX_PORT='8081'
KNP_NGINX_DIR='/mnt/knowtmp/project1/p1_nginx-6sp'
KNP_NGINX_CONF='autoindex/'
KNP_NGINX_CONSTRAINT_URL='knowcluster03.dyndns.org'

KNP_NEO4J_PORT='7475'
KNP_NEO4J_DIR='/mnt/knowstorage/project1/p1_neo4j-7475'

```

## add symlinks
```
ln -s /workspace/knowtmp/ /mnt/
ln -s /workspace/knowstorage/ /mnt/
```

## copy pipeline code
```
cd $KNP_WORKING_DIR
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
```
```
cd KnowNet_Pipeline/
git checkout chronos_testing
```

## build the documentation
```
cd $KNP_WORKING_DIR/docs/
make html
```
```
cd $KNP_WORKING_DIR
```

## MySQL setup
### start MySQL database if it is not running
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute "drop database KnowNet;"
```

## Redis setup
### start Redis database if it is not running
```
python3 code/redis_utilities.py \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
    -rd $KNP_REDIS_DIR -rps $KNP_REDIS_PASS -rcu $KNP_REDIS_CONSTRAINT_URL\
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
```
### empty Redis database if it is running
```
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS BGREWRITEAOF
```

## nginx setup
### start nginx server if it is not running
```
mkdir $KNP_NGINX_DIR
mkdir $KNP_NGINX_DIR/data/
mkdir $KNP_NGINX_DIR/docs/
python3 code/nginx_utilities.py \
    -ngp $KNP_NGINX_PORT -ncu $KNP_NGINX_CONSTRAINT_URL \
    -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
```

## clear the chronos queue
```
for c in $KNP_CHRONOS_URL ; do
    curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep '"name"' | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
    for s in 'map-' 'table-' 'check-' 'fetch-' 'import-' 'KN_starter' ; do
        echo $s
        for i in `grep "$s" /tmp/t.txt  `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
        done;
    done;
done;
```

## clear any existing files
```
rm -r $KNP_LOGS_PATH/*
rm -r $KNP_DATA_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_LOGS_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_DATA_PATH/*
```

## run setup pipeline (time: 2hr 30min)
```
python3 code/workflow_utilities.py CHECK -su \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES
```

## run parse pipeline (time: 2hr)
```
python3 code/workflow_utilities.py CHECK \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## run import pipeline (time: 2hr 45min) 
```
python3 code/workflow_utilities.py IMPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## create report of results
```
cp -r $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map $KNP_STORAGE_DIR/$KNP_DATA_PATH/id_map
code/reports/enumerate_files.sh $KNP_STORAGE_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
    $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
git add -f tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
git commit -m 'adding result report'
git push
```
## create user
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
    -P $KNP_MYSQL_PORT --execute \
    "CREATE USER 'KNviewer' IDENTIFIED BY 'dbdev249'; \
    GRANT SELECT ON KnowNet.* TO 'KNviewer';"
```

# cleanup
## move databases to knowstorage
stop the marathon redis and mysql jobs
```
KNP_STORAGE_MYSQL=$KNP_STORAGE_DIR'/p1_mysql-3307'
KNP_STORAGE_REDIS=$KNP_STORAGE_DIR'/p1_redis-6380'
mv $KNP_MYSQL_DIR $KNP_STORAGE_MYSQL
mv $KNP_REDIS_DIR $KNP_STORAGE_REDIS
```
start new marathon redis and mysql jobs
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_STORAGE_MYSQL -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
python3 code/redis_utilities.py \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
    -rd $KNP_STORAGE_REDIS -rps $KNP_REDIS_PASS -rcu $KNP_REDIS_CONSTRAINT_URL\
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -wd $KNP_WORKING_DIR
```

## neo4j setup
### start neo4j server if it is not running
```

mkdir $KNP_NEO4J_DIR
mkdir $KNP_NEO4J_DIR/data
mkdir $KNP_NEO4J_DIR/shared
docker run -dt --restart=always --name hdfs sequenceiq/hadoop-docker:latest /etc/bootstrap.sh -bash
docker run -d --restart=always --name mazerunner --link hdfs:hdfs kbastani/neo4j-graph-analytics:latest
docker run -dt --restart=always --name p1_neo4j-$KNP_NEO4J_PORT \
    -p $KNP_NEO4J_PORT:7474 --link mazerunner:mazerunner --link hdfs:hdfs \
    -v $KNP_NEO4J_DIR/data:/opt/data -v $KNP_NEO4J_DIR/shared:/shared \
    kbastani/docker-neo4j
```

### dump data from MySQL for species
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT taxon AS taxonQID, sp_abbrev AS abbrev, \
    sp_sciname AS sci_name, \"Species\" AS QLABEL FROM KnowNet.species s" | \
    sed 's/QID/:ID(Species)/g' | sed 's/QLABEL/:LABEL/g' > \
    $KNP_NEO4J_DIR/shared/neo4j.species.txt;
```
### dump data from MySQL for nodes
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT UCASE(node_id) AS node_idQID, n_alias AS alias, \
    n_type_desc AS QLABEL FROM KnowNet.node n, KnowNet.node_type nt \
    WHERE n.n_type_id=nt.n_type_id" | sed 's/QID/:ID(Node)/g' | \
    sed 's/QLABEL/:LABEL/g' > $KNP_NEO4J_DIR/shared/neo4j.nodes.txt;
```
### dump data from MySQL for node-species relationships
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT UCASE(n.node_id) AS QSTART_ID, taxon AS QEND_ID, \
    \"InGenome\" AS QTYPE FROM KnowNet.node_species ns, KnowNet.node n \
    WHERE n.node_id=ns.node_id AND n.n_type_id = 1 " | \
    sed 's/QSTART_ID/:START_ID(Node)/g' | sed 's/QEND_ID/:END_ID(Species)/g' | \
    sed 's/QTYPE/:TYPE/g' > $KNP_NEO4J_DIR/shared/neo4j.species_edges.txt;
```
### format data from unique.edge.txt for edges
```
awk -v OFS="\t" 'BEGIN { print ":START_ID(Node)", \
    ":END_ID(Node)", "weight", ":TYPE" }; \
    { print toupper($1), toupper($2), $4, $3 }; END {}'\
    $KNP_STORAGE_DIR/$KNP_DATA_PATH/unique.edge.txt > \
    $KNP_NEO4J_DIR/shared/neo4j.edges.txt
```
### format data from unique.node_meta for node_meta
```
awk -v OFS="\t" 'BEGIN { print "node_id", "n_type_desc", "info_type", \
    "info_desc" }; { print toupper($1), "Property", $2, $3 }; END {}'\
    $KNP_STORAGE_DIR/$KNP_DATA_PATH/unique.node_meta.txt > \
    $KNP_NEO4J_DIR/shared/neo4j.node_meta.txt
```
### dump data from MySQL for edge_meta
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT --quick \
    --execute "SELECT DISTINCT UCASE(s.n1_id), UCASE(s.n2_id), s.et_name, em.info_type, \
    em.info_desc FROM KnowNet.status s, KnowNet.edge_meta em, \
    KnowNet.edge_type et WHERE s.line_hash = em.line_hash \
    AND s.status_desc = 'mapped'; " > $KNP_NEO4J_DIR/shared/neo4j.edge_meta.dmp
sort -u $KNP_NEO4J_DIR/shared/neo4j.edge_meta.dmp > \
    $KNP_NEO4J_DIR/shared/neo4j.edge_meta.txt
```

### import data

#### remove old database
```
docker exec p1_neo4j-$KNP_NEO4J_PORT rm -rf /opt/data/graph.db
```
#### insert uniq nodes and production edges (time: 7m)
```
docker exec p1_neo4j-$KNP_NEO4J_PORT /var/lib/neo4j/bin/neo4j-import \
    --into /opt/data/graph.db --nodes /shared/neo4j.species.txt \
    --nodes /shared/neo4j.nodes.txt \
    --relationships /shared/neo4j.species_edges.txt \
    --relationships /shared/neo4j.edges.txt --delimiter "TAB"
```
#### add meta_data to nodes and edges (skipped)
```
cp $KNP_WORKING_DIR/code/neo4j/import.cypher $KNP_NEO4J_DIR/shared/
docker exec p1_neo4j-$KNP_NEO4J_PORT /var/lib/neo4j/bin/neo4j-shell \
    -path /opt/data/graph.db -file /shared/import.cypher
```
#### start new database 
```
docker restart p1_neo4j-$KNP_NEO4J_PORT
```

