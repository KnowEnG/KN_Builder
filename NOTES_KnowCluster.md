# Full Pipeline Run
### (on knowcluster01 in /workspace/knowtmp/project1/)

## Set environment variables
```
KNP_CHRONOS_URL='knowcluster01.dyndns.org:4400'
KNP_LOCAL_DIR='/workspace/knowtmp/project1/KnowNet_Pipeline'
KNP_CLOUD_DIR='/mnt/knowtmp/project1/KnowNet_Pipeline'
KNP_SHARE_DIR='/mnt/knowstorage/project1'
KNP_DATA_PATH='data_tests'
KNP_LOGS_PATH='logs_tests'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MARATHON_URL='knowcluster01.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knowcluster05.dyndns.org'
KNP_MYSQL_PORT='3307'
KNP_MYSQL_DIR='/mnt/knowtmp/project1/p1_mysql-3307'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='10000'
KNP_MYSQL_CPU='2.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL='knowcluster05.dyndns.org'

KNP_REDIS_HOST='knowcluster07.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_REDIS_DIR='/mnt/knowtmp/project1/p1_redis-6380'
KNP_REDIS_MEM='8000'
KNP_REDIS_CPU='2.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL='knowcluster07.dyndns.org'

KNP_NGINX_PORT='8081'
KNP_NGINX_DIR='/mnt/knowtmp/project1/p1_nginx-tests'
KNP_NGINX_CONF='autoindex/'
KNP_NGINX_CONSTRAINT_URL='knowcluster03.dyndns.org'

```

## add symlinks
```
ln -s /workspace/knowtmp/ /mnt/
ln -s /workspace/knowstorage/ /mnt/
```

## copy pipeline code
```
cd $(dirname $KNP_LOCAL_DIR)
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
```
```
cd KnowNet_Pipeline/
git checkout chronos_testing
```

## build the documentation
```
cd $KNP_LOCAL_DIR/docs/
make html
```
```
cd $KNP_LOCAL_DIR
```

## MySQL setup
### start MySQL database if it is not running
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -ld $KNP_LOCAL_DIR
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute "drop database KnowNet;"
```

## Redis setup
### start Redis database if it is not running
```
python3 code/redis_utilities.py \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
    -rd $KNP_REDIS_DIR -rps $KNP_REDIS_PASS -rcu $KNP_REDIS_CONSTRAINT_URL\
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -ld $KNP_LOCAL_DIR
```
### empty Redis database if it is running
```
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
```

## nginx setup
### start nginx server if it is not running
```
mkdir $KNP_NGINX_DIR
mkdir $KNP_NGINX_DIR/docs/
python3 code/nginx_utilities.py \
    -ngp $KNP_NGINX_PORT -ncu $KNP_NGINX_CONSTRAINT_URL \
    -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
    -m $KNP_MARATHON_URL -cd $KNP_CLOUD_DIR -ld $KNP_LOCAL_DIR
```

## clear the chronos queue
```
for c in $KNP_CHRONOS_URL ; do
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
    -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR \
    -sd $KNP_SHARE_DIR
```

## create report of results
```
code/reports/enumerate_files.sh $KNP_LOCAL_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
    $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03build.$KNP_DATA_PATH.pipe
```
## create user
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
    -P $KNP_MYSQL_PORT --execute \
    "CREATE USER 'KNviewer' IDENTIFIED BY 'dbdev249'; \
    GRANT SELECT ON KnowNet.* TO 'KNviewer';"
```
## dump data into nginx (on KnowNBS)
```
mysqldump -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    KnowNet | gzip > $KNP_NGINX_DIR/data/KnowNet.dump.sql.gz
cat $KNP_REDIS_DIR/appendonly.aof | gzip > $KNP_NGINX_DIR/data/appendonly.aof.gz
tar czvf $KNP_NGINX_DIR/data/KnowNet.tgz $KNP_LOCAL_DIR
```
