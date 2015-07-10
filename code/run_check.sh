#!/bin/bash

# assume that master container is given a volume at "/shared/" that contains an
# code/ folder with .py scripts and a raw_downloads/ folder for raw files.  
mkdir -p /shared/code/
mkdir -p /shared/raw_downloads/
rm -r /shared/jobs/
mkdir -p /shared/jobs/

# print out command for new container for each source specific *.py
BASE="\/mnt\/users\/blatti\/apps\/P1_source_check\/"   # change users to storage for cluster
CMD="sh -c 'cd /code/; /usr/bin/time -v python3 SRC.py;'" 
IMG="cblatti3\/python3:0.1"
ctr=1
CURL="curl -L -H 'Content-Type: application/json' -X POST -d /shared/jobs/NUM_SRC.json 192.17.58.180:4400/scheduler/iso8601"

for i in `ls /shared/code/*.py | sed -e 's/.py//g' | sed -e 's/\/shared\/code\///g' | sort`; do  
	echo "$i"
	
	# skip non-source specific files
	if [ "$i" == "utilities" ]; then
		continue;
	fi
	
	# create job json
	cat /shared/template.json | sed -e "s/NUM/$ctr/g" | sed -e "s/BASE/$BASE/g" | sed -e "s/SRC/$i/g" | sed -e "s/IMG/$IMG/g" >> /shared/jobs/$ctr\_$i.json;

	# record correspnding docker command
	echo "docker run -v $BASE/code/:/code/ -v $BASE/raw_downloads/:/raw_downloads/ $IMG $CMD" | sed -e "s/SRC/$i/g" >> /shared/jobs/docker_cmds.txt

	# set up and send the curl command
	CURL_CMD=$(echo $CURL | sed -e "s/NUM/$ctr/g" | sed -e "s/SRC/$i/g")
	echo $CURL_CMD
#	$($CURL_CMD)
	
	ctr=$(($ctr + 1))

done;
