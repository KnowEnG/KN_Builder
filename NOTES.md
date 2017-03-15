# Full Pipeline Run
### (on knowcluster01 in /workspace/knowtmp/project1/)

## Set environment variables
```
KNP_CHRONOS_URL='knowcluster01.dyndns.org:4400'
KNP_CODE_DIR='/mnt/backup/knowdata/KnowNets/KnowNet_0.3/KN-20rep-1702/'
KNP_WORKING_DIR=$KNP_CODE_DIR'/'
KNP_STORAGE_DIR="$KNP_WORKING_DIR"
KNP_DB_DIR="$KNP_WORKING_DIR"
KNP_BUILD_NAME='20rep-1702'
KNP_DATA_PATH='data_'$KNP_BUILD_NAME
KNP_LOGS_PATH='logs_'$KNP_BUILD_NAME
KNP_ENS_SPECIES='RESEARCH'

KNP_BUCKET="userKN-$KNP_BUILD_NAME"
KNP_MARATHON_URL='knowcluster01.dyndns.org:8080/v2/apps'

# KNP_MYSQL_HOST='knowcluster07.dyndns.org'
# KNP_MYSQL_PORT='3306'
# KNP_MYSQL_DIR=$KNP_DB_DIR'/p1mysql-'$KNP_MYSQL_PORT'-'$KNP_BUILD_NAME
# KNP_MYSQL_CONF='build_conf/'
# KNP_MYSQL_MEM='10000'
# KNP_MYSQL_CPU='2.0'
# KNP_MYSQL_PASS='KnowEnG'
# KNP_MYSQL_CONSTRAINT_URL='knowcluster07.dyndns.org'

export KNP_MYSQL_HOST='knownbs.cxtvettjrq71.us-west-2.rds.amazonaws.com'
export KNP_MYSQL_USER='blatti'
export KNP_MYSQL_PASS='knowdev249'
export KNP_MYSQL_PORT='3306'
export KNP_MYSQL_DB='KnowNet'

export KNP_REDIS_HOST='knowcluster07.dyndns.org'
export KNP_REDIS_PORT='6379'
export KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_DIR=$KNP_DB_DIR'/redis-'$KNP_BUILD_NAME
KNP_REDIS_MEM='8000'
KNP_REDIS_CPU='2.0'
KNP_REDIS_CONSTRAINT_URL='knowcluster07.dyndns.org'

KNP_NGINX_PORT='8081'
KNP_NGINX_DIR=$KNP_DB_DIR'/p1nginx-'$KNP_NGINX_PORT'-'$KNP_BUILD_NAME
KNP_NGINX_CONF='autoindex/'
KNP_NGINX_CONSTRAINT_URL='knowcluster05.dyndns.org'

KNP_NEO4J_PORT='7474'
KNP_NEO4J_DIR=$KNP_DB_DIR'/p1neo4j-'$KNP_NEO4J_PORT'-'$KNP_BUILD_NAME
KNP_NEO4J_NAME=$(basename $KNP_NEO4J_DIR)
```

## add symlinks
```
mkdir -p /mnt/backup
ln -s /workspace/knowdata /mnt/backup/
```

## copy pipeline code
```
cd "$KNP_CODE_DIR"
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
```
```
cd KnowNet_Pipeline/
```

## clear any existing files
```
rm -r $KNP_STORAGE_DIR/$KNP_LOGS_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_DATA_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_BUCKET/*
```

## MySQL setup
### start MySQL database if it is not running
```
# python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR \
    -sd $KNP_STORAGE_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -u $KNP_MYSQL_USER -p$KNP_MYSQL_PASS \
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
### build the documentation
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline/docs/
make html
```
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline
```

### start nginx server if it is not running
```
mkdir $KNP_NGINX_DIR
mkdir $KNP_NGINX_DIR/data/
mkdir $KNP_NGINX_DIR/docs/
python3 code/nginx_utilities.py \
    -ngp $KNP_NGINX_PORT -ncu $KNP_NGINX_CONSTRAINT_URL \
    -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH
```

## clear the chronos queue
```
for c in $KNP_CHRONOS_URL ; do
    curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep '"name"' | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
    for s in 'export-' 'import-' 'map-' 'table-' 'fetch-' 'check-' 'KN_starter'  ; do
        echo $s
        for i in `grep "$s" /tmp/t.txt  `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
        done;
    done;
done;
```

## run setup pipeline (time: 2hr 30min)
```
python3 code/workflow_utilities.py CHECK -su \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES
```

## run parse pipeline (time: 2hr)
```
python3 code/workflow_utilities.py CHECK \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## run import pipeline (time: 2hr 45min)
```
python3 code/workflow_utilities.py IMPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## run export pipeline (time: )
```
mkdir $KNP_WORKING_DIR/$KNP_BUCKET
cp code/mysql/edge_type.txt $KNP_WORKING_DIR/$KNP_BUCKET

## add gene maps
head -n-1 $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map/species/species.txt > $KNP_WORKING_DIR/$KNP_BUCKET/species.txt
for TAXON in `cut -f1 $KNP_WORKING_DIR/$KNP_BUCKET/species.txt `; do
    echo $TAXON;
    mkdir -p $KNP_WORKING_DIR/$KNP_BUCKET/Species/$TAXON;
    mysql -h$KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P$KNP_MYSQL_PORT -D$KNP_MYSQL_DB -e "\
        SELECT ns.node_id \
        FROM node_species ns \
        WHERE ns.taxon = $TAXON \
        ORDER BY ns.node_id" \
        | tail -n +2 > $KNP_WORKING_DIR/$KNP_BUCKET/Species/$TAXON/$TAXON.glist;
        LANG=C.UTF-8 python3 code/conv_utilities.py -mo LIST \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            $KNP_WORKING_DIR/$KNP_BUCKET/Species/$TAXON/$TAXON.glist;
        rm $KNP_WORKING_DIR/$KNP_BUCKET/Species/$TAXON/$TAXON.glist;
done

## add subnetworks
mysql -h$KNP_MYSQL_HOST -p$KNP_MYSQL_PASS -u$KNP_MYSQL_USER -P$KNP_MYSQL_PORT -DKnowNet -e "\
   SELECT et.n1_type, ns2.taxon, e.et_name, count(1) \
   FROM edge e, edge_type et, node_species ns2 \
   WHERE e.et_name=et.et_name \
   AND e.n2_id=ns2.node_id \
   GROUP BY et.n1_type, ns2.taxon, e.et_name" \
   > $KNP_WORKING_DIR/$KNP_BUCKET/db_contents.txt
head -n1 $KNP_WORKING_DIR/$KNP_BUCKET/db_contents.txt \
    > $KNP_WORKING_DIR/$KNP_BUCKET/directories.txt
awk -v x=125000 '$4 >= x' $KNP_WORKING_DIR/$KNP_BUCKET/db_contents.txt \
    | grep "^Gene" >> $KNP_WORKING_DIR/$KNP_BUCKET/directories.txt
awk -v x=4000 '$4 >= x' $KNP_WORKING_DIR/$KNP_BUCKET/db_contents.txt \
    | grep "^Property" >> $KNP_WORKING_DIR/$KNP_BUCKET/directories.txt
python3 code/workflow_utilities.py EXPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL -b $KNP_BUCKET\
    -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES \
    -p "$(tail -n+2 $KNP_WORKING_DIR/$KNP_BUCKET/directories.txt \
        | cut -f2,3 \
        | sed -e 's/\t/::/g' \
        | sed -e ':a;N;$!ba;s/\n/,,/g')"

## extract Property node maps
for CLASS1 in Property; do
    for line in `grep $CLASS1 $KNP_WORKING_DIR/$KNP_BUCKET/directories.txt | sed 's#\t#/#g'` ; do
        echo $line;
        CLASS=$(echo $line | cut -f1 -d/)
        TAXON=$(echo $line | cut -f2 -d/)
        ETYPE=$(echo $line | cut -f3 -d/)
        grep Property $KNP_WORKING_DIR/$KNP_BUCKET/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.node_map > $KNP_WORKING_DIR/$KNP_BUCKET/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.pnode_map
    done
done;

# set up your AWS credentials
mkdir ~/.aws
echo -e "[default]\naws_access_key_id = ABC\naws_secret_access_key = XYZ" > ~/.aws/credentials
# modify with your keys

# copy directory to S3 bucket
pip install awscli
aws s3 sync --delete $KNP_WORKING_DIR/$KNP_BUCKET s3://$KNP_BUCKET
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
mysql -h $KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS \
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
mysql -h $KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT taxon AS taxonQID, sp_abbrev AS abbrev, \
    sp_sciname AS sci_name, \"Species\" AS QLABEL FROM KnowNet.species s" | \
    sed 's/QID/:ID(Species)/g' | sed 's/QLABEL/:LABEL/g' > \
    $KNP_NEO4J_DIR/shared/neo4j.species.txt;
```
### dump data from MySQL for nodes
```
mysql -h $KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    --execute "SELECT DISTINCT UCASE(node_id) AS node_idQID, n_alias AS alias, \
    n_type AS QLABEL FROM KnowNet.node n " | sed 's/QID/:ID(Node)/g' | \
    sed 's/QLABEL/:LABEL/g' > $KNP_NEO4J_DIR/shared/neo4j.nodes.txt;
```
### dump data from MySQL for node-species relationships
```
mysql -h $KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
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
mysql -h $KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT --quick \
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

