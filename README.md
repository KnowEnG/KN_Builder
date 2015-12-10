## Running Locally
### set environment variables
```
KNP_LOCAL_DIR='/workspace/apps/KnowNet_Pipeline'
KNP_DATA_PATH='local_pipe'
KNP_MYSQL_HOST='knowcharles.dyndns.org'
KNP_REDIS_HOST='knowcharles.dyndns.org'
KNP_CHRONOS_URL='mmaster01.cse.illinois.edu:4400'
KNP_SRC='dip'
KNP_ALIAS='PPI'
KNP_CHUNK='1'
```

### running single step locally inside p1_cloud9 dev environment

#### check for updates to remote file for source named $KNP_SRC
  - *updates file_metadata json and mysql*
```
KNP_CMD="python3 code/check_utilities.py $KNP_SRC -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST"
echo $KNP_CMD
```

#### fetch remote files for alias named $KNP_ALIAS of source $KNP_SRC
  - *for ontology files, extracts mapping dictionary and imports into redis,
        extracts nodes and node_metadata and imports into mysql, updates
        file_metadata json and mysql*
  - *for data files, creates .rawline. chunks and imports to mysql, updates
        file_metadata json and mysql*
  - *for ensembl, imports mysql database, extracts gene mappings into redis,
        imports nodes into mysql, updates file_metadata json and mysql*
```
cd $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS
KNP_CMD="python3 ../../../code/fetch_utilities.py file_metadata.json \
    -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```

#### table for chunk CHUNK of alias named $KNP_ALIAS of source $KNP_SRC
  - *converts .rawline. file into 11 column description .edge. file to prepare
        edges for entity mapping, also created edge and node metadata files as
        necessary and sort, uniques them*
```
cd $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS
KNP_CMD="python3 ../../../code/table_utilities.py \
    chunks/$KNP_SRC.$KNP_ALIAS.rawfile.$KNP_CHUNK.txt file_metadata.json \
    -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR"
echo $KNP_CMD
```

#### entity mapping for chunk CHUNK of alias named $KNP_ALIAS of source $KNP_SRC
  - *converts .edge. file into 6 column description .conv. file and .status.
        file using redis, sorts and uniques .conv. and .edge2line., and inserts
        .conv., .node_meta., .edge_meta., and .edge2line. file into mysql*
```
KNP_CMD="python3 code/conv_utilities.py \
    $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS/chunks/$KNP_SRC.$KNP_ALIAS.edge.$KNP_CHUNK.txt \
    -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```

### running multiple steps locally inside p1_cloud9 dev environment
#### setup databases and entity mapping
may first want to
clear out mysql:
```
KNP_CMD="mysql -h $KNP_MYSQL_HOST --port 3306 -uroot -pKnowEnG KnowNet \
    --execute \"drop database KnowNet;\""
echo $KNP_CMD
```
clear out redis:
```
KNP_CMD="redis-cli -h $KNP_REDIS_HOST -a KnowEnG FLUSHDB"
echo $KNP_CMD
```
##### check all remote sources for updates
  - *updates file_metadata json and mysql*
```
KNP_CMD="python3 code/setup_utilities.py CHECK LOCAL STEP -dp $KNP_DATA_PATH \
     -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
##### fetch all updated setup files from remote sources, process ontologies and databases
```
KNP_CMD="python3 code/setup_utilities.py FETCH LOCAL STEP -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
##### run full setup pipeline without redoing ensembl
```
KNP_CMD="python3 code/setup_utilities.py CHECK LOCAL PIPELINE -dp $KNP_DATA_PATH -ne \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
###### takes about 36 minutes

#### pipeline local
##### check for remote sources updates
```
KNP_CMD="python3 code/pipeline_utilities.py CHECK LOCAL STEP -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST"
echo $KNP_CMD
```
##### fetch updated files from remote sources, process ontologies
```
KNP_CMD="python3 code/pipeline_utilities.py FETCH LOCAL STEP -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
##### 'table' raw files to standard table format
```
KNP_CMD="python3 code/pipeline_utilities.py TABLE LOCAL STEP -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR"
echo $KNP_CMD
```
##### map entries to KN entities and produce edges and metadata files
```
KNP_CMD="python3 code/pipeline_utilities.py MAP LOCAL STEP -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
##### run full sources pipeline
```
KNP_CMD="python3 code/pipeline_utilities.py CHECK LOCAL PIPELINE -dp $KNP_DATA_PATH \
    -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST -rh $KNP_REDIS_HOST"
echo $KNP_CMD
```
##### about 45 minutes

## Running On Cloud
### running all steps in cloud mode
#### setup cloud pipeline
```
python3 code/setup_utilities.py CHECK CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -rh knowice.cs.illinois.edu -rp 6380 -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe
```
##### about 22 minutes

#### pipeline cloud pipeline
```
python3 code/pipeline_utilities.py CHECK CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -rh knowice.cs.illinois.edu -rp 6380 -dp cloud_pipe
```
##### about 24 minutes


### running one full step in cloud mode
#### setup cloud all fetch
```
for i in ensembl ppi species; do
echo $i
python3 code/setup_utilities.py FETCH CLOUD STEP -dp cloud_pipe -p $i \
    -ld /workspace/prototype/KnowNet_Pipeline/ \
    -rh knowcharles.dyndns.org -myh knowcharles.dyndns.org \
    -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ \
; done;
```

#### pipeline cloud all fetch
```
for i in `ls code/srcClass/*py | sed 's#code/srcClass/##g' | sed 's#.py##g'`; do echo $i; python3 code/pipeline_utilities.py FETCH CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done;
```

#### pipeline cloud all table
```
for i in `ls -d cloud_pipe/*/*/chunks | sed 's#cloud_pipe/##g' | sed 's#/chunks##g' | sed 's#/#,#g'  `; do echo $i; python3 code/pipeline_utilities.py TABLE CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/  -rh knowice.cs.illinois.edu -rp 6380 -p $i -dp cloud_pipe; done;
```

#### pipeline cloud all conv
```
for i in `ls cloud_pipe/*/*/chunks/*.edge.* | sed 's#cloud_pipe/##g' | sed 's#/chunks##g' | sed 's#/#\t#g' | cut -f3  `; do echo $i; python3 code/pipeline_utilities.py MAP CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done
```


### cloud cleanup
#### when complete, be a good citizen and remove jobs from the cloud
```
for i in `ls code/chron_jobs/*json | sed "s#code/chron_jobs/##g" | sed "s/.json//g"` ; do CMD="curl -L -X DELETE mmaster01.cse.illinois.edu:4400/scheduler/job/$i"; echo "$CMD"; eval $CMD; done
```

#### delete ALL P1 jobs on prototype cloud - USE CAREFULLY
```
for c in 'mmaster01.cse.illinois.edu:4400' 'knowmaster.dyndns.org:4400'; do
    curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep name | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
    for s in 'check-' 'fetch-' 'table-' 'conv-'; do
        echo $s
        for i in `grep "$s" /tmp/t.txt  `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
        done;
    done;
done;
```

## checks and reports
### quick check for completeness
```
code/reports/enumerate_files.sh local_pipe/
```



