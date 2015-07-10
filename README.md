docker build -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1

docker run -it -v /mnt/users/blatti/apps/P1_source_check/:/shared/ ubuntu /shared/code/run_check.sh 

cat jobs/docker_cmds.txt
