#!/bin/bash

SRC=$1
DATA_DIR=$2
CODE_DIR=$3
RUN_TYPE=$4 # LOCAL, CONTAIN, CLOUD

SRC_DIR="$DATA_DIR/$SRC"

CLOUD_BASE="/mnt/storage/blatti/apps/P1_source_check/"   # toplevel directory on cloud

CMD1="sh -c 'cd ALIASDIR/; /usr/bin/time -v python3 CODEDIR/fetch_utilities.py file_metadata.json;'" # command for current step of pipeline
CMD2="sh -c 'cd ALIASDIR/; /usr/bin/time -v python3 CODEDIR/fetch_utilities.py file_metadata.json;'" # command for current and next step of pipeline

CMD_TYPE="STEP"  # STEP or PIPELINE

IMG="cblatti3/python3:0.1" 
CTR=1
CURL="curl -i -L -H 'Content-Type: application/json' -X POST -d@CODEDIR/chron_jobs/TMPJOB.json mmaster01.cse.illinois.edu:4400/scheduler/iso8601"

CMD=$CMD1
if [ "$CMD_TYPE" == "PIPELINE" ]; then
	CMD=$CMD2;
fi

echo "$RUN_TYPE $CMD_TYPE"

## loop through all aliases of source
for ALIAS in `ls -d $SRC_DIR/* | sed "s#$SRC_DIR/##g" | sort`; do  
	echo "$ALIAS"
	
	ALIAS_DIR="$SRC_DIR/$ALIAS"
	
	if [ "$RUN_TYPE" == "LOCAL" ]; then
		LOCAL_CMD=$(echo $CMD | sed "s#ALIASDIR#$ALIAS_DIR#g" | sed "s#CODEDIR#$CODE_DIR#g" | sed -e "s/TMPNUM/$CTR/g" | sed -e "s/TMPALIAS/$ALIAS/g")
		echo $LOCAL_CMD
		eval $LOCAL_CMD
	fi

	if [ "$RUN_TYPE" == "CONTAIN" ]; then
		echo "not implemented"
		#CONTAIN_CMD=$(echo "docker rm check_TMPNUM_TMPSRC; docker run --name check_TMPNUM_TMPSRC -rm -v $LOCAL_BASE/code/:/code/ -v $LOCAL_BASE/raw_downloads/:/raw_downloads/ $IMG $CMD" | sed -e "s/TMPNUM/$CTR/g" | sed "s#TMPBASE#/#g" | sed -e "s/TMPSRC/$ALIAS/g")
		#echo $CONTAIN_CMD
		#eval $CONTAIN_CMD
	fi

	if [ "$RUN_TYPE" == "CLOUD" ]; then
		JOBNAME=$(echo "alias_fetch_$SRC.$CTR.$ALIAS" | sed "s#\.#_#g")
		mkdir -p $CODE_DIR/chron_jobs/
		cat $CODE_DIR/fetch_template.json | sed "s#IMG#$IMG#g" | sed "s#TMPCMD#$CMD#g" | sed "s#ALIASDIR#/data/#g" | sed "s#CODEDIR#/code/#g" | sed "s#ALIAS_DIR#$ALIAS_DIR/#g" | sed "s#CODE_DIR#$CODE_DIR/#g" | sed "s#CLOUDBASE#$CLOUD_BASE#g" | sed "s#TMPJOB#$JOBNAME#g" > $CODE_DIR/chron_jobs/$JOBNAME.json;
		CLOUD_CMD=$(echo $CURL | sed "s#CODEDIR#$CODE_DIR/#g" | sed "s#TMPJOB#$JOBNAME#g")
		echo $CLOUD_CMD
		eval $CLOUD_CMD
	fi

	CTR=$(($CTR + 1))

done;