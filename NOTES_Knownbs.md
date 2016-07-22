# Full Pipeline Run
### (on knownbs in /workspace/storage)

## Set environment variables
```
KNP_CHRONOS_URL='knownbs.dyndns.org:4400'
KNP_WORKING_DIR='/workspace/storage/project1'
KNP_STORAGE_DIR=''
KNP_DB_DIR=$KNP_WORKING_DIR
KNP_BUILD_NAME='representative'
KNP_DATA_PATH='data_'$KNP_BUILD_NAME
KNP_LOGS_PATH='logs_'$KNP_BUILD_NAME
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MARATHON_URL='knownbs.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knownbs.dyndns.org'
KNP_MYSQL_PORT='3306'
KNP_MYSQL_DIR=$KNP_DB_DIR'/p1mysql-'$KNP_MYSQL_PORT'-'$KNP_BUILD_NAME
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='10000'
KNP_MYSQL_CPU='2.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL=''

KNP_REDIS_HOST='knownbs.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_REDIS_DIR=$KNP_DB_DIR'/p1redis-'$KNP_REDIS_PORT'-'$KNP_BUILD_NAME
KNP_REDIS_MEM='8000'
KNP_REDIS_CPU='2.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL=''

KNP_NGINX_PORT='8282'
KNP_NGINX_DIR=$KNP_DB_DIR'/p1nginx-'$KNP_NGINX_PORT'-'$KNP_BUILD_NAME
KNP_NGINX_CONF='autoindex/'

KNP_NEO4J_PORT='7475'
KNP_NEO4J_DIR=$KNP_DB_DIR'/p1neo4j-'$KNP_NEO4J_PORT'-'$KNP_BUILD_NAME

```

## add symlinks
```
ln -s /workspace/storage/ /mnt/
```

## copy pipeline code
```
cd $KNP_WORKING_DIR
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
```
```
cd KnowNet_Pipeline/
```

## build the documentation
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline/docs/
make html
```
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline
```

## MySQL setup
### start MySQL database if it is not running
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH \
    -lp $KNP_LOGS_PATH
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
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH
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
mkdir $KNP_NGINX_DIR/docs/
mkdir $KNP_NGINX_DIR/data/
python3 code/nginx_utilities.py \
    -ngp $KNP_NGINX_PORT \
    -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH
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

## run setup pipeline
```
python3 code/workflow_utilities.py CHECK -su \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES
```

## run parse pipeline
```
python3 code/workflow_utilities.py CHECK \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## run import pipeline
```
python3 code/workflow_utilities.py IMPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## create report of results
```
code/reports/enumerate_files.sh $KNP_WORKING_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
    $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03-NBS-build.$KNP_DATA_PATH.pipe
git add -f tests/KN03-NBS-build.$KNP_DATA_PATH.pipe
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

## neo4j setup
### start neo4j server if it is not running
```

mkdir $KNP_NEO4J_DIR
mkdir $KNP_NEO4J_DIR/data
mkdir $KNP_NEO4J_DIR/shared
docker run -dt --restart=always --name hdfs sequenceiq/hadoop-docker:latest /etc/bootstrap.sh -bash
docker run -d --restart=always --name mazerunner --link hdfs:hdfs kbastani/neo4j-graph-analytics:latest
docker run -dt --restart=always --name $KNP_NEO4J_NAME \
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
    n_type AS QLABEL FROM KnowNet.node n " | sed 's/QID/:ID(Node)/g' | \
    sed 's/QLABEL/:LABEL/g' > $KNP_NEO4J_DIR/shared/neo4j.nodes.txt;
```
### dump data from MySQL for node-species relationships
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT UCASE(n.node_id) AS QSTART_ID, taxon AS QEND_ID, \
    \"InGenome\" AS QTYPE FROM KnowNet.node_species ns, KnowNet.node n \
    WHERE n.node_id=ns.node_id AND n.n_type = 'Gene' " | \
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
### format data from unique.node_meta for node_meta (skipped)
```
awk -v OFS="\t" 'BEGIN { print "node_id", "n_type_desc", "info_type", \
    "info_desc" }; { print toupper($1), "Property", $2, $3 }; END {}'\
    $KNP_STORAGE_DIR/$KNP_DATA_PATH/unique.node_meta.txt > \
    $KNP_NEO4J_DIR/shared/neo4j.node_meta.txt
```
### dump data from MySQL for edge_meta (skipped)
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
docker exec $KNP_NEO4J_NAME rm -rf /opt/data/graph.db
```
#### insert uniq nodes and production edges (time: 7m)
```
docker exec $KNP_NEO4J_NAME /var/lib/neo4j/bin/neo4j-import \
    --into /opt/data/graph.db --nodes /shared/neo4j.species.txt \
    --nodes /shared/neo4j.nodes.txt \
    --relationships /shared/neo4j.species_edges.txt \
    --relationships /shared/neo4j.edges.txt --delimiter "TAB"
```
#### add meta_data to nodes and edges (skipped)
```
cp $KNP_WORKING_DIR/code/neo4j/import.cypher $KNP_NEO4J_DIR/shared/
docker exec $KNP_NEO4J_NAME /var/lib/neo4j/bin/neo4j-shell \
    -path /opt/data/graph.db -file /shared/import.cypher
```
#### start new database 
```
docker restart $KNP_NEO4J_NAME
```

# Transfer data to KnowNet (skipped)
## dump data into nginx (on KnowNBS)
```
mysqldump -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    KnowNet | gzip > $KNP_NGINX_DIR/data/KnowNet.$KNP_BUILD_NAME.dump.sql.gz
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS BGREWRITEAOF
cat $KNP_REDIS_DIR/appendonly.aof | gzip > $KNP_NGINX_DIR/data/appendonly.aof.gz
cd $KNP_WORKING_DIR
tar czvf $KNP_NGINX_DIR/data/KnowNet.tgz $(basename $KNP_WORKING_DIR)
```

## Set environment variables
```
KNP_WORKING_DIR='/workspace/KnowNet_0.3/KnowNet_Pipeline'
KNP_DATA_PATH='data_representative'
KNP_LOGS_PATH='logs_representative'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MYSQL_HOST='knownet.dyndns.org'
KNP_MYSQL_PORT='3306'
KNP_MYSQL_DIR='/project1/KnowNet_0.3/p1_mysql'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_MEM='4G'

KNP_REDIS_HOST='knownet.dyndns.org'
KNP_REDIS_PORT='6379'
KNP_REDIS_DIR='/project1/KnowNet_0.3/p1_redis'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_MEM='2G'


KNP_NGINX_HOST='knownbs.dyndns.org'
KNP_NGINX_PORT='8282'
KNP_NGINX_DIR='/project1/KnowNet_0.3/p1_nginx'
KNP_NGINX_CONF='autoindex/'
KNP_NGINX_HOST2='knowcluster03.dyndns.org'
KNP_NGINX_PORT2='8081'
```

## symlink directory
```
ln -s /workspace/ /project1
```
## Download the data
### Download KnowNet_Pipeline directory
```
mkdir $KNP_WORKING_DIR
cd $KNP_WORKING_DIR
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/KnowNet.tgz
tar xzvf KnowNet.tgz
```
### Download Redis data (from knownbs - 6 species)
```
mkdir $KNP_REDIS_DIR && cd $KNP_REDIS_DIR
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/appendonly.aof.gz
gunzip -d appendonly.aof.gz
```
### Download Redis data (from knowcluster - human only)
```
mkdir $KNP_REDIS_DIR && cd $KNP_REDIS_DIR
wget $KNP_NGINX_HOST2:$KNP_NGINX_PORT2/data/appendonly.aof
```
### Download MySQL data
```
mkdir $KNP_MYSQL_DIR && cd $KNP_WORKING_DIR
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/KnowNet.dump.sql.gz
```

## MySQL setup 
### start MySQL database if it is not running
```
docker run -d --restart=on-failure:5 --name p1_mysql-$KNP_MYSQL_PORT \
    -e MYSQL_ROOT_PASSWORD=$KNP_MYSQL_PASS -p $KNP_MYSQL_PORT:3306 \
    -m $KNP_MYSQL_MEM -v $KNP_MYSQL_DIR:/var/lib/mysql \
    -v $KNP_CLOUD_DIR/code/mysql/$KNP_MYSQL_CONF:/etc/mysql/conf.d/ mysql
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute "drop database KnowNet;"
```

### load the downloaded data
```
cd $KNP_WORKING_DIR
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
    -P $KNP_MYSQL_PORT -e "CREATE DATABASE KnowNet;"
gunzip < KnowNet.dump.sql.gz | mysql -h $KNP_MYSQL_HOST -uroot \
    -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT KnowNet
```

## Redis setup
### start Redis database if it is not running
```
docker run -d --restart=on-failure:5 --name p1_redis-$KNP_REDIS_PORT \
    -m $KNP_REDIS_MEM -p $KNP_REDIS_PORT:6379 -v $KNP_REDIS_DIR:/data \
    redis redis-server --appendonly yes --requirepass $KNP_REDIS_PASS
```
### restart the Redis database if it is running
```
docker restart p1_redis-$KNP_REDIS_PORT
```

## nginx setup
### start nginx server if it is not running
```
docker run -d --restart=on-failure:5 --name p1_nginx-$KNP_NGINX_PORT \
    -p $KNP_NGINX_PORT:80 \
    -v $KNP_NGINX_DIR:/usr/share/nginx/html \
    -v $KNP_CLOUD_DIR/docs/_build/html/:/usr/share/nginx/html/docs \
    -v $KNP_CLOUD_DIR/code/nginx/$KNP_NGINX_CONF:/etc/nginx/conf.d/ \
    nginx


