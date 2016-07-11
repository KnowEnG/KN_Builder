# Full Pipeline Run
### (on knowcluster01 in /workspace/knowtmp/project1/)

## Set environment variables
```
KNP_CHRONOS_URL='knowcluster01.dyndns.org:4400'
KNP_WORKING_DIR='/workspace/knowtmp/project1'
KNP_STORAGE_DIR='/mnt/knowstorage/project1'
KNP_DATA_PATH='data_rep_vert_metazoa'
KNP_LOGS_PATH='logs_rep_vert_metazoa'
KNP_ENS_SPECIES='REPRESENTATIVE,,METAZOA,,VERTEBRATES'

KNP_MARATHON_URL='knowcluster01.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knowcluster05.dyndns.org'
KNP_MYSQL_PORT='3308'
KNP_MYSQL_DIR='/mnt/knowstorage/project1/p1_mysql-3308'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='35000'
KNP_MYSQL_CPU='4.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL='knowcluster05.dyndns.org'

KNP_REDIS_HOST='knowcluster07.dyndns.org'
KNP_REDIS_PORT='6381'
KNP_REDIS_DIR='/mnt/knowstorage/project1/p1_redis-6381'
KNP_REDIS_MEM='25000'
KNP_REDIS_CPU='4.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL='knowcluster07.dyndns.org'

KNP_NGINX_PORT='8081'
KNP_NGINX_DIR='/mnt/knowtmp/project1/p1_nginx-6sp'
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
cd $KNP_WORKING_DIR
git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
```
```
cd KnowNet_Pipeline/
```

## build the documentation
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline/docs/
make html
```
```
cd $KNP_WORKING_DIR/KnowNet_Pipeline
```


## clear any existing files
```
rm -r $KNP_LOGS_PATH/*
rm -r $KNP_DATA_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_LOGS_PATH/*
rm -r $KNP_STORAGE_DIR/$KNP_DATA_PATH/*
```

## MySQL setup
### start MySQL database if it is not running
```
python3 code/mysql_utilities.py \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
    -myps $KNP_MYSQL_PASS -mycu $KNP_MYSQL_CONSTRAINT_URL \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR \
    -sd $KNP_STORAGE_DIR -dp $KNP_DATA_PATH
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
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
```
### empty Redis database if it is running
```
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS BGREWRITEAOF
```

## nginx setup
### start nginx server if it is not running
```
mkdir $KNP_NGINX_DIR
mkdir $KNP_NGINX_DIR/data/
mkdir $KNP_NGINX_DIR/docs/
python3 code/nginx_utilities.py \
    -ngp $KNP_NGINX_PORT -ncu $KNP_NGINX_CONSTRAINT_URL \
    -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
    -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR
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

## run setup pipeline (time: 4hr 15min)
```set fetch usage to 25GB in components.json```
```
python3 code/workflow_utilities.py CHECK -su \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES
```

## run parse pipeline (time: 24hr 30min)
```set fetch usage to 12 GB in components.json```
```
python3 code/workflow_utilities.py CHECK \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## run import pipeline (time: 32hr 15min) 
```
python3 code/workflow_utilities.py IMPORT \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL \
    -sd $KNP_STORAGE_DIR
```

## create report of results
```
cp -r $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map $KNP_STORAGE_DIR/$KNP_DATA_PATH/id_map
code/reports/enumerate_files.sh $KNP_STORAGE_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
    $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
git add -f tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
git commit -m 'adding result report'
git push
```
## create user
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
    -P $KNP_MYSQL_PORT --execute \
    "CREATE USER 'KNviewer' IDENTIFIED BY 'dbdev249'; \
    GRANT SELECT ON KnowNet.* TO 'KNviewer';"
```