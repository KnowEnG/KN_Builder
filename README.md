docker build -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1

docker run --name check_master -d -v /mnt/users/blatti/apps/P1_source_check/:/shared/ tutum/curl /shared/code/run_check.sh 

cat jobs/docker_cmds.txt

# for testing
docker run --name check_master -it -v /mnt/users/blatti/apps/P1_source_check/:/shared/ tutum/curl /bin/bash 
/shared/code/run_check.sh 