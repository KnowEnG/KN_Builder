### Build correct image
```
docker build -f Dockerfile -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1
```

```
docker build -f Dockerfile.mysql -t cblatti3/py3_mysql:0.1 .
docker push cblatti3/py3_mysql:0.1
```

```
docker build -f Dockerfile.redis.mysql -t cblatti3/py3_redis_mysql:0.1 .
docker push cblatti3/py3_redis_mysql:0.1
```


### running single step outside of docker
#### check for updates to remote file for source named SRC
  *- updates file_metadata json and mysql*
```
python3 code/check_utilities.py SRC -dp DATA_PATH -ld LOCAL_DIR -myh MYSQL_HOST
```

#### fetch remote files for alias named ALIAS of source SRC
  *- for ontology files, extracts mapping dictionary and imports into redis,
        extracts nodes and node_metadata and imports into mysql, updates
        file_metadata json and mysql
  - for data files, creates .rawline. chunks and imports to mysql, updates
        file_metadata json and mysql
  - for ensembl, imports mysql database, extracts gene mappings into redis,
        imports nodes into mysql, updates file_metadata json and mysql*
```
cd DATA_PATH/SRC/ALIAS
python3 ../../../code/fetch_utilities.py file_metadata.json -dp DATA_PATH \
    -ld LOCAL_DIR -myh MYSQL_HOST -rh REDIS_HOST
```

#### table for chunk CHUNK of alias named ALIAS of source SRC
    - converts .rawline. file into 11 column description .edge. file to prepare
        edges for entity mapping, also created edge and node metadata files as
        necessary and sort, uniques them
```
cd DATA_PATH/SRC/ALIAS
python3 ../../../code/table_utilities.py chunks/SRC.ALIAS.rawfile.CHUNK.txt \
    file_metadata.json -dp DATA_PATH -ld LOCAL_DIR
```

#### entity mapping for chunk CHUNK of alias named ALIAS of source SRC
    - converts .edge. file into 6 column description .conv. file and .status.
        file using redis, sorts and uniques .conv. and .edge2line., and inserts
        .conv., .node_meta., .edge_meta., and .edge2line. file into mysql
```
python3 code/conv_utilities.py DATA_PATH/SRC/ALIASchunks/SRC.ALIAS.edge.CHUNK.txt \
    -dp DATA_PATH -ld LOCAL_DIR -myh MYSQL_HOST -rh REDIS_HOST
```

### running all steps in local mode
#### setup
may want to
clear out mysql:
```
mysql -h MYSQL_HOST --port 3306 -uroot -pKnowEnG KnowNet \
    --execute "drop database KnowNet;"
```
clear out redis:
```
redis-cli -h REDIS_HOST -a KnowEnG FLUSHDB
```
##### check for remote sources updates
```
python3 code/setup_utilities.py CHECK LOCAL STEP -dp local_pipe \
     -ld /workspace/apps/KnowNet_Pipeline/ \
     -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### fetch updated files from remote sources, process ontologies and databases
```
python3 code/setup_utilities.py FETCH LOCAL STEP -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
###### 20,462,422 redis keys
##### run full setup pipeline without ensembl
```
python3 code/setup_utilities.py CHECK LOCAL PIPELINE -dp local_pipe -ne \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
###### about 36 minutes

#### pipeline local
##### check for remote sources updates
```
python3 code/pipeline_utilities.py CHECK LOCAL STEP -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### fetch updated files from remote sources, process ontologies
```
python3 code/pipeline_utilities.py FETCH LOCAL STEP -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### convert files to standard table format
```
python3 code/pipeline_utilities.py TABLE LOCAL STEP -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### map entries to KN entities and produce edges and metadata files
```
python3 code/pipeline_utilities.py MAP LOCAL STEP -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### run full sources pipeline
```
python3 code/pipeline_utilities.py CHECK LOCAL PIPELINE -dp local_pipe \
    -ld /workspace/apps/KnowNet_Pipeline/ \
    -myh knowcharles.dyndns.org -rh knowcharles.dyndns.org
```
##### about 45 minutes


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

### quick check for completeness
```
code/reports/enumerate_files.sh local_pipe/
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


