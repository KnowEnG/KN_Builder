#### Build correct image

docker build -f Dockerfile -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1

docker build -f Dockerfile.mysql -t cblatti3/py3_mysql:0.1 .
docker push cblatti3/py3_mysql:0.1


#### running outside of docker
# check for source named SRC
cd /workspace/apps/P1_source_check/code/
python SRC.py

# fetch for alias named ALIAS of source SRC
cd /workspace/apps/P1_source_check/raw_downloads/SRC/ALIAS
python /workspace/apps/P1_source_check/fetch_utilities.py file_metadata.json


#### running inside container with requirements
docker run --name check_master -it -v /mnt/users/blatti/apps/P1_source_check/:/shared/ cblatti3/py3_mysql:0.1 /bin/bash

# running whole pipeline while inside container
/shared/code/run_check.sh LOCAL PIPELINE

# running only check while inside container
/shared/code/run_check.sh LOCAL STEP

# running only fetch while inside container
for i in `ls /shared/raw_downloads/`; do /shared/code/run_fetch.sh $i /shared/raw_downloads/ /shared/code/ LOCAL; done
for i in `ls /shared/raw_downloads/`; do /shared/code/run_fetch.sh $i /shared/raw_downloads/ /shared/code/ CLOUD; done

#### running on KnowEnG cloud

# running whole pipeline on the cloud
./code/run_check.sh CLOUD PIPELINE
# when complete, be a good citizen and remove jobs from the cloud
for i in `ls code/chron_jobs/*json | sed "s#code/chron_jobs/##g" | sed "s/.json//g"` ; do CMD="curl -L -X DELETE mmaster01.cse.illinois.edu:4400/scheduler/job/$i"; echo "$CMD"; eval $CMD; done

# delete ALL jobs on production and development chronos queue
for c in \
'mmaster02.cse.illinois.edu:4400' \
'192.17.177.186:4400' \
; do
    for i in `curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep name | sed 's#{"name":"##g' | sed 's#"##g' `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
    done;
done;

#### running with python
./code/pipeline_utilities.py CHECK LOCAL PIPELINE -ld /mnt/users/blatti/apps/P1_source_check -dp raw_downloads


./code/pipeline_utilities.py CHECK CLOUD STEP -c 192.17.177.186:4400 -ld /mnt/users/blatti/apps/P1_source_check/ -cd /mnt/storage/blatti/apps/P1_source_check/ -cp code -dp raw_downloads



## setup check local
python3 code/setup_utilities.py CHECK LOCAL STEP -ld /workspace/apps/P1_source_check/ -dp set_local_step2

## setup fetch local
python3 code/setup_utilities.py FETCH LOCAL STEP -ld /workspace/apps/P1_source_check/ -dp set_local_step2

# setup local pipeline
python3 code/setup_utilities.py CHECK LOCAL PIPELINE -ld /workspace/apps/P1_source_check/ -dp set_local_pipe

## setup check cloud
python3 code/setup_utilities.py CHECK CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp set_cloud_step4

# setup fetch cloud
python3 code/setup_utilities.py FETCH CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp set_cloud_step4 -p ensembl

# setup cloud pipeline
python3 code/setup_utilities.py CHECK CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp set_cloud_pipe 


## pipeline check local
python3 code/pipeline_utilities.py CHECK LOCAL STEP -ld /workspace/prototype/ -dp pipe_local_step2

## pipeline fetch local
python3 code/pipeline_utilities.py FETCH LOCAL STEP -ld /workspace/prototype/ -dp pipe_local_step2

## pipeline table local
python3 code/pipeline_utilities.py TABLE LOCAL STEP -ld /workspace/prototype/ -dp pipe_local_step2

# pipeline local pipeline
python3 code/pipeline_utilities.py CHECK LOCAL PIPELINE -ld /workspace/prototype/ -dp pipe_local_pipe

## pipeline check cloud
python3 code/pipeline_utilities.py CHECK CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp pipe_cloud_step2

## pipeline fetch cloud
python3 code/pipeline_utilities.py FETCH CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp pipe_cloud_step2 -p kegg

# pipeline cloud pipeline
python3 code/pipeline_utilities.py FETCH CLOUD PIPELINE -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ -ld /workspace/prototype/ -dp pipe_cloud_pipe 
