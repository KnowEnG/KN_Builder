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
for INST in mysql,3306 mysql_lincs,3307 mysql_perf,3308; do
    echo $INST;
    TMPPATH=`echo $INST | cut -f1 -d,`
    TMPPORT=`echo $INST | cut -f2 -d,`
    JOB=`cat code/dockerfiles/marathon/mysql.json | sed -e 's/TMPPATH/'"$TMPPATH"'/g' | sed -e 's/TMPPORT/'"$TMPPORT"'/g'`
    echo $JOB
    curl -X POST -H "Content-type: application/json" knowcluster01.dyndns.org:8080/v2/apps -d"$JOB"
done;

### restart
curl -X POST knowcluster01.dyndns.org:8080/v2/apps/p1mysql/restart

### delete
curl -X DELETE knowcluster01.dyndns.org:8080/v2/apps/p1mysql

### check loaded
for INST in mysql,3306 mysql_lincs,3307 mysql_perf,3308; do
    echo $INST;
    TMPPORT=`echo $INST | cut -f2 -d,`
    mysql -hknowcluster01.dyndns.org -uroot -pKnowEnG --port $TMPPORT --execute "show databases";
done

## For cloud9
### deploy
for USER in project1,8181 mparat2,8282 pvijaya2,8383; do

for USER in blatti,8484 post3,8585; do
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
for USER in blatti,8484 post3,8585; do
    TMPID=`echo $USER | cut -f1 -d,`
    curl -X DELETE knowcluster01.dyndns.org:8080/v2/apps/"$TMPID"-c9/restart
done;
