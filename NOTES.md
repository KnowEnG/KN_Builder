# Full Pipeline Run
### (on knownbs in /workspace/storage)

## Set environment variables
```
KNP_CHRONOS_URL='knownbs.dyndns.org:4400'
KNP_LOCAL_DIR='/workspace/storage/project1/KnowNet_Pipeline'
KNP_CLOUD_DIR='/mnt/storage/project1/KnowNet_Pipeline'
KNP_SHARE_DIR=''
KNP_DATA_PATH='data_representative'
KNP_LOGS_PATH='logs_representative'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MARATHON_URL='knownbs.dyndns.org:8080/v2/apps'

KNP_MYSQL_HOST='knownbs.dyndns.org'
KNP_MYSQL_PORT='3307'
KNP_MYSQL_DIR='/mnt/storage/project1/p1_mysql'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_MEM='10000'
KNP_MYSQL_CPU='2.0'
KNP_MYSQL_PASS='KnowEnG'
KNP_MYSQL_CONSTRAINT_URL=''

KNP_REDIS_HOST='knownbs.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_REDIS_DIR='/mnt/storage/project1/p1_redis'
KNP_REDIS_MEM='8000'
KNP_REDIS_CPU='2.0'
KNP_REDIS_PASS='KnowEnG'
KNP_REDIS_CONSTRAINT_URL=''

KNP_NGINX_PORT='8282'
KNP_NGINX_DIR='/mnt/storage/project1/p1_nginx'
KNP_NGINX_CONF='autoindex/'
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
    -ngp $KNP_NGINX_PORT \
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
git add tests/KN03build.$KNP_DATA_PATH.pipe
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
## dump data into nginx (on KnowNBS)
```
mysqldump -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT \
    KnowNet | gzip > $KNP_NGINX_DIR/data/KnowNet.dump.sql.gz
cat $KNP_REDIS_DIR/appendonly.aof | gzip > $KNP_NGINX_DIR/data/appendonly.aof.gz
tar czvf $KNP_NGINX_DIR/data/KnowNet.tgz $KNP_LOCAL_DIR
```

# Transfer data to KnowNet

## Set environment variables
```
KNP_LOCAL_DIR='/workspace/KnowNet_0.3/KnowNet_Pipeline'
KNP_DATA_PATH='data_representative'
KNP_LOGS_PATH='logs_representative'
KNP_ENS_SPECIES='REPRESENTATIVE'

KNP_MYSQL_HOST='knowet.dyndns.org'
KNP_MYSQL_PORT='3306'
KNP_MYSQL_DIR='/project1/KnowNet_0.3/p1_mysql'
KNP_MYSQL_CONF='build_conf/'
KNP_MYSQL_PASS='KnowEnG'

KNP_REDIS_HOST='knowet.dyndns.org'
KNP_REDIS_PORT='6379'
KNP_REDIS_DIR='/project1/KnowNet_0.3/p1_redis'
KNP_REDIS_PASS='KnowEnG'

KNP_NGINX_HOST='knownbs.dyndns.org'
KNP_NGINX_PORT='8081'
KNP_NGINX_DIR='/project1/KnowNet_0.3/p1_nginx'
KNP_NGINX_CONF='autoindex/'
```

## symlink directory
```
ln -s /workspace/ /project
```
## Download the data
```
mkdir $(dirname $KNP_LOCAL_DIR)
cd $(dirname $KNP_LOCAL_DIR)
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/KnowNet.tgz
tar xzvf KnowNet.tgz
mkdir $KNP_REDIS_DIR && cd $KNP_REDIS_DIR
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/appendonly.aof.gz
gunzip -d appendonly.aof.gz
mkdir $KNP_MYSQL_DIR && cd $KNP_MYSQL_DIR
wget $KNP_NGINX_HOST:$KNP_NGINX_PORT/data/KnowNet.dump.sql.gz
```

## MySQL setup 
### start MySQL database if it is not running
```
docker run -d --restart=always --name p1_mysql-$KNP_MYSQL_PORT \
    -e MYSQL_ROOT_PASSWORD=$KNP_MYSQL_PASS -p $KNP_MYSQL_PORT:3306 \
    -v $KNP_MYSQL_DIR:/var/lib/mysql \
    -v $KNP_LOCAL_DIR/code/mysql/$KNP_MYSQL_CONF:/etc/mysql/conf.d/ mysql
```

### empty MySQL database if it is running
```
mysql -h $KNP_MYSQL_HOST -uroot -p$KNP_MYSQL_PASS \
        -P $KNP_MYSQL_PORT --execute "drop database KnowNet;"
```

### load the downloaded data
```
cd $KNP_MYSQL_DIR
gunzip < KnowNet.dump.sql.gz | mysql -h $KNP_MYSQL_HOST -uroot \
    -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT KnowNet
```

## Redis setup
### start Redis database if it is not running
```
docker run -d --restart=always --name p1_redis-$KNP_REDIS_PORT \
    -p $KNP_REDIS_PORT:6379 -v $KNP_REDIS_DIR:/data \
    redis redis-server --appendonly yes --requirepass $KNP_REDIS_PASS
```
### restart the Redis database if it is running
```
docker restart p1_redis-$KNP_REDIS_PORT
```

## nginx setup
### start nginx server if it is not running
```
docker run -d --restart=always --name p1_nginx-$KNP_NGINX_PORT \
    -p $KNP_NGINX_PORT:80 \
    -v $KNP_NGINX_DIR:/usr/share/nginx/html \
    -v $KNP_LOCAL_DIR/docs/_build/html/:/usr/share/nginx/html/docs \
    -v $KNP_LOCAL_DIR/code/nginx/$KNP_NGINX_CONF:/etc/nginx/conf.d/ \
    nginx
    

