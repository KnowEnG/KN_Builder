docker build -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1

docker run --name check_master -d -v /mnt/users/blatti/apps/P1_source_check/:/shared/ tutum/curl /shared/code/run_check.sh 

cat jobs/docker_cmds.txt

# for testing
docker run --name check_master -it -v /mnt/users/blatti/apps/P1_source_check/:/shared/ tutum/curl /bin/bash 
/shared/code/run_check.sh 


# for running outside of docker
# check for source named SRC
cd /workspace/apps/P1_source_check/code/
python SRC.py

# fetch for alias named ALIAS of source SRC
cd /workspace/apps/P1_source_check/raw_downloads/SRC/ALIAS
python /workspace/apps/P1_source_check/fetch_code/utilities.py file_metadata.json


# running pipeline on the cloud 
./code/run_check.sh CLOUD PIPELINE
# when complete, be a good citizen and remove jobs from the cloud
for i in `ls code/chron_jobs/*json | sed "s#code/chron_jobs/##g" | sed "s/.json//g"` ; do CMD="curl -L -X DELETE mmaster02.cse.illinois.edu:4400/scheduler/job/$i"; echo "$CMD"; eval $CMD; done                
# running pipeline outside containers
./code/run_check.sh LOCAL PIPELINE

# running only check outside containers
./code/run_check.sh LOCAL STEP

# running only check in local containers
./code/run_check.sh CONTAIN STEP

