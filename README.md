#### Build correct image

docker build -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1


#### running outside of docker
# check for source named SRC
cd /workspace/apps/P1_source_check/code/
python SRC.py

# fetch for alias named ALIAS of source SRC
cd /workspace/apps/P1_source_check/raw_downloads/SRC/ALIAS
python /workspace/apps/P1_source_check/fetch_utilities.py file_metadata.json


#### running inside container with requirements
docker run --name check_master -it -v /mnt/users/blatti/apps/P1_source_check/:/shared/ cblatti3/python3:0.1 /bin/bash

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

#### running with python
./code/pipeline_utilities.py CHECK LOCAL PIPELINE -ld /mnt/users/blatti/apps/P1_source_check -dp raw_downloads  
