# Full Pipeline Run 
### (on knownbs in /workspace/storage)

## Set environment variables 
```
KNP_CHRONOS_URL='knownbs.dyndns.org:4400'
KNP_LOCAL_DIR='/workspace/storage/project1/KnowNet_Pipeline/'
KNP_CLOUD_DIR='/mnt/storage/project1/KnowNet_Pipeline/'
KNP_SHARE_DIR=''
KNP_DATA_PATH='data_representative'
KNP_LOGS_PATH='logs_representatvie'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MARATHON_URL='http://knownbs.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knownbs.dyndns.org'
KNP_MYSQL_PORT='3307'
KNP_MYSQL_DIR='/mnt/storage/project1/p1_mysql'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='15000'
KNP_MYSQL_CPU='4.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL=''

KNP_REDIS_HOST='knownbs.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_REDIS_DIR='/mnt/storage/project1'
KNP_REDIS_MEM='15000'
KNP_REDIS_CPU='4.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL=''
```

## copy pipeline code
```
cd $KNP_LOCAL_DIR
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
cd KnowNet_Pipeline/
git checkout chronos_testing
```

## MySQL setup
### start MySQL database if it is not running
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF -myps $KNP_MYSQL_PASS\
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -ld $KNP_LOCAL_DIR
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute \"drop database KnowNet;\"
```

## Redis setup
### start Redis database
```
python3 code/redis_utilities.py \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
    -rd $KNP_REDIS_DIR -rps $KNP_REDIS_PASS\
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -ld $KNP_LOCAL_DIR
```
### empty Redis database if it is running
```
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
```

## clear the chronos queue
```
for c in 'knowcluster01.dyndns.org:4400' ; do
    curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep '"name"' | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
    for s in 'map-' 'table-' 'check-' 'fetch-' 'import-' 'KN_starter' ; do
        echo $s
        for i in `grep "$s" /tmp/t.txt  `; do
            CMD="curl -L -X DELETE $c/scheduler/job/$i";
            echo "$CMD";
            eval "$CMD";
        done;
    done;
done;
```

## clear any existing files
```
rm -r $KNP_LOGS_PATH/*
rm -r $KNP_DATA_PATH/*
rm -r $KNP_SHARE_DIR/$KNP_LOGS_PATH/*
rm -r $KNP_SHARE_DIR/$KNP_DATA_PATH/*
```

## run setup pipeline 
```
python3 code/workflow_utilities.py CHECK -su \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -ld $KNP_LOCAL_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR \
    -sd $KNP_SHARE_DIR -es $KNP_ENS_SPECIES
```

## run parse pipeline 
```
python3 code/workflow_utilities.py CHECK \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -ld $KNP_LOCAL_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR \
    -sd $KNP_SHARE_DIR
```

## run import pipeline
```
python3 code/workflow_utilities.py IMPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -ld $KNP_LOCAL_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR
    -sd $KNP_SHARE_DIR
```

## create user
```
KNP_CMD="mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute \
        \"CREATE USER 'KNviewer' IDENTIFIED BY 'dbdev249'; \
        GRANT SELECT ON KnowNet.* TO 'KNviewer';\""
echo $KNP_CMD
```

