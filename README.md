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
#### check for source named SRC
```
cd /workspace/apps/P1_source_check/code/
python SRC.py
```

#### fetch for alias named ALIAS of source SRC
```
cd P1_source_check/data/SRC/ALIAS
python3 ../../../code/fetch_utilities.py file_metadata.json
```

#### table for alias named ALIAS of source SRC
```
cd P1_source_check/data/SRC/ALIAS
python3 ../../../code/table_utilities.py chunks/SRC.ALIAS.rawfile.1.txt file_metadata.json
```


### running all steps in local mode
#### setup local pipeline
```
python3 code/setup_utilities.py CHECK LOCAL PIPELINE -ld /workspace/apps/P1_source_check/ -dp local_pipe -rh knowice.cs.illinois.edu -rp 6380
```
##### about 36 minutes

#### pipeline local pipeline
```
python3 code/pipeline_utilities.py CHECK LOCAL PIPELINE -ld /workspace/apps/P1_source_check/ -dp local_pipe -rh knowice.cs.illinois.edu -rp 6380
```
##### about 45 minutes


### running all steps in cloud mode
#### setup cloud pipeline
```
python3 code/setup_utilities.py CHECK CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -rh knowice.cs.illinois.edu -rp 6380 -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe3
```
##### about 22 minutes

#### setup cloud all fetch
```
for i in ensembl ppi species; do python3 code/setup_utilities.py FETCH CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -rh knowice.cs.illinois.edu -rp 6380 -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -p $i; done
```

#### pipeline cloud pipeline
```
python3 code/pipeline_utilities.py CHECK CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380
```
##### about 24 minutes

#### pipeline cloud all fetch
```
for i in `ls code/srcClass/*py | sed 's#code/srcClass/##g' | sed 's#.py##g'`; do echo $i; python3 code/pipeline_utilities.py FETCH CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done; 
```

#### pipeline cloud all table
```
for i in `ls -d cloud_pipe/*/*/chunks | sed 's#cloud_pipe/##g' | sed 's#/chunks##g' | sed 's#/#,#g'  `; do echo $i; python3 code/pipeline_utilities.py TABLE CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done;
```

#### pipeline cloud all conv
```
for i in `ls cloud_pipe/*/*/chunks/*.edge.* | sed 's#cloud_pipe/##g' | sed 's#/chunks##g' | sed 's#/#\t#g' | cut -f3  `; do echo $i; python3 code/pipeline_utilities.py MAP CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done
```




#### when complete, be a good citizen and remove jobs from the cloud
```
for i in `ls code/chron_jobs/*json | sed "s#code/chron_jobs/##g" | sed "s/.json//g"` ; do CMD="curl -L -X DELETE mmaster01.cse.illinois.edu:4400/scheduler/job/$i"; echo "$CMD"; eval $CMD; done
```

#### delete ALL jobs on prototype cloud - USE CAREFULLY
```
for c in \
'mmaster01.cse.illinois.edu:4400' \
; do
    for i in `curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep name | sed 's#{"name":"##g' | sed 's#"##g' `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
    done;
done;
```










