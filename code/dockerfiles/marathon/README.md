## For Redis
### deploy
for i in 7; do
    echo $i;
    JOB=`cat code/dockerfiles/marathon/redis.json | sed -e 's/TMPNUM/'"$i"'/g'`
    echo $JOB
    curl -X POST -H "Content-type: application/json" knowcluster01.dyndns.org:8080/v2/apps -d"$JOB"
done;

### restart
curl -X POST knowcluster01.dyndns.org:8080/v2/apps/p1redis/restart

### delete
curl -X DELETE knowcluster01.dyndns.org:8080/v2/apps/p1redis

### check loaded
for i in {1..7}; do
    redis-cli -h knowcluster0"$i".dyndns.org -p 6379 -a KnowEnG info | tail -n1;
done

## For MySQL

### deploy
for INST in mysql_perf,3307; do
    echo $INST;
    TMPPATH=`echo $INST | cut -f1 -d,`
    TMPPORT=`echo $INST | cut -f2 -d,`
    JOB=`cat code/dockerfiles/marathon/mysql.json | sed -e 's/TMPPATH/'"$TMPPATH"'/g' | sed -e 's/TMPPORT/'"$TMPPORT"'/g'`
    echo $JOB
    curl -X POST -H "Content-type: application/json" knowcluster01.dyndns.org:8080/v2/apps -d"$JOB"
done;

### deploy with build mysql conf
for INST in p1_mysql,3306; do
    echo $INST;
    TMPPATH=`echo $INST | cut -f1 -d,`
    TMPPORT=`echo $INST | cut -f2 -d,`
    JOB=`cat code/dockerfiles/marathon/mysql_build.json | sed -e 's/TMPPATH/'"$TMPPATH"'/g' | sed -e 's/TMPPORT/'"$TMPPORT"'/g'`
    echo $JOB
    curl -X POST -H "Content-type: application/json" knowcluster01.dyndns.org:8080/v2/apps -d"$JOB"
done;

KNP_CHRONOS_URL='knownbs.dyndns.org:4400'
KNP_LOCAL_DIR='/workspace/storage/project1/'
KNP_CLOUD_DIR='/mnt/storage/project1'
KNP_SHARE_DIR=''
KNP_DATA_PATH='data_representative'
KNP_LOGS_PATH='logs_representatvie'
KNP_MYSQL_HOST='knownbs.dyndns.org'
KNP_MYSQL_PORT='3307'
KNP_REDIS_HOST='knownbs.dyndns.org'
KNP_REDIS_PORT='6380'
KNP_ENS_SPECIES='REPRESENTATIVE'
KNP_MARATHON_URL='http://knownbs.dyndns.org:8080/v2/apps'
KNP_MYSQL_DIR='/mnt/storage/project1/p1_mysql'
KNP_MYSQL_CONF='build_conf'
KNP_REDIS_PATH='/mnt/storage/project1'
KNP_MYSQL_MEM='15000'
KNP_MYSQL_CPU='4.0'

KNP_CMD="python3 code/mysql_utilities.py \
    -m $KNP_MARATHON_URL \
    -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
    -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU
    -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF
    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
    -ld $KNP_LOCAL_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
    -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR \
    -sd $KNP_SHARE_DIR -es $KNP_ENS_SPECIES"
echo $KNP_CMD




### restart
curl -X POST knowcluster01.dyndns.org:8080/v2/apps/p1mysql/restart

### delete
curl -X DELETE knowcluster01.dyndns.org:8080/v2/apps/p1mysql

### check loaded
mysql -hknowcluster01.dyndns.org -uroot -pKnowEnG --port 3306 --execute "show databases";

## For cloud9
### deploy
for USER in project1,8282 analytics,8383 blatti,8484 post3,8585; do
for USER in project1,8282 analytics,8383; do
    echo $USER;
    TMPID=`echo $USER | cut -f1 -d,`
    TMPPORT=`echo $USER | cut -f2 -d,`
    JOB=`cat code/dockerfiles/marathon/cloud9.json | sed -e 's/TMPPORT/'"$TMPPORT"'/g' | sed -e 's/TMPID/'"$TMPID"'/g'`
    echo $JOB
    curl -X POST -H "Content-type: application/json" knowcluster01.dyndns.org:8080/v2/apps -d"$JOB"
done;

### restart
for USER in blatti,8484 post3,8585; do
    TMPID=`echo $USER | cut -f1 -d,`
    curl -X POST knowcluster01.dyndns.org:8080/v2/apps/"$TMPID"-c9/restart
done;

### delete
for USER in project1,8282 analytics,8383; do
    TMPID=`echo $USER | cut -f1 -d,`
    curl -X DELETE knowcluster01.dyndns.org:8080/v2/apps/"$TMPID"-c9
done;
