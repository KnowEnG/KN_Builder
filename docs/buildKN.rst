Building the Knowledge Network
******************************

Set environment variables
-------------------------

.. code:: bash

        KNP_CHRONOS_URL='127.0.0.1:8888'
        KNP_BUILD_NAME='20rep-1706'
        KNP_CODE_DIR="/data/"
        KNP_WORKING_DIR=$KNP_CODE_DIR'/'
        KNP_STORAGE_DIR="$KNP_WORKING_DIR"
        KNP_DB_DIR="$KNP_WORKING_DIR"
        KNP_DATA_PATH='data_'$KNP_BUILD_NAME
        KNP_LOGS_PATH='logs_'$KNP_BUILD_NAME
        KNP_ENS_SPECIES='homo_sapiens'
        
        KNP_BUCKET="KnowNets/KN-$KNP_BUILD_NAME"
        KNP_S3_DIR="$KNP_WORKING_DIR/$KNP_BUCKET/"
        KNP_EXPORT_DIR="$KNP_S3_DIR/userKN-$KNP_BUILD_NAME"
        KNP_MARATHON_URL='127.0.0.1:8080/v2/apps'
        
        export KNP_MYSQL_HOST='127.0.0.1'
        export KNP_MYSQL_PORT='3306'
        export KNP_MYSQL_PASS='KnowEnG'
        export KNP_MYSQL_USER='root'
        export KNP_MYSQL_DB='KnowNet'
        KNP_MYSQL_DIR=$KNP_DB_DIR'/mysql-'$KNP_MYSQL_PORT'-'$KNP_BUILD_NAME
        KNP_MYSQL_CONF='build_conf/'
        KNP_MYSQL_MEM='10000'
        KNP_MYSQL_CPU='0.5'
        KNP_MYSQL_CONSTRAINT_URL='127.0.0.1'
        
        #export KNP_MYSQL_HOST='knownet.cxtvettjrq71.us-west-2.rds.amazonaws.com'
        #export KNP_MYSQL_USER='p1user'
        #export KNP_MYSQL_PASS='knowdev249'
        #export KNP_MYSQL_PORT='3306'
        #export KNP_MYSQL_DB='KnowNet'
        
        export KNP_REDIS_HOST='127.0.0.1'
        export KNP_REDIS_PORT='6379'
        export KNP_REDIS_PASS='KnowEnG'
        KNP_REDIS_DIR=$KNP_DB_DIR'/redis-'$KNP_REDIS_PORT'-'$KNP_BUILD_NAME
        KNP_REDIS_MEM='8000'
        KNP_REDIS_CPU='0.5'
        KNP_REDIS_CONSTRAINT_URL='127.0.0.1'
        
        KNP_NGINX_PORT='8081'
        KNP_NGINX_DIR=$KNP_DB_DIR'/nginx-'$KNP_NGINX_PORT'-'$KNP_BUILD_NAME
        KNP_NGINX_CONF='autoindex/'
        KNP_NGINX_CONSTRAINT_URL='127.0.0.1'
        
        KNP_NEO4J_PORT='7474'
        KNP_NEO4J_DIR=$KNP_DB_DIR'/neo4j-'$KNP_NEO4J_PORT'-'$KNP_BUILD_NAME
        KNP_NEO4J_NAME=$(basename $KNP_NEO4J_DIR)

Add symlinks
------------

.. code:: bash

       mkdir -p /mnt/backup
       ln -s /workspace/knowdata /mnt/backup/

Copy pipeline code
------------------

.. code:: bash

        cd "$KNP_CODE_DIR"
        git clone https://github.com/KnowEnG/KnowNet_Pipeline.git
        cd KnowNet_Pipeline/

Clear any existing files
------------------------

.. code:: bash

        rm -r $KNP_STORAGE_DIR/$KNP_LOGS_PATH/*
        rm -r $KNP_STORAGE_DIR/$KNP_DATA_PATH/*
        rm -r $KNP_STORAGE_DIR/$KNP_BUCKET/*

MySQL setup
-----------

Start MySQL database if it is not running

.. code:: bash

        python3 code/mysql_utilities.py \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -mym $KNP_MYSQL_MEM -myc $KNP_MYSQL_CPU \
            -myd $KNP_MYSQL_DIR -mycf $KNP_MYSQL_CONF \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER -mycu $KNP_MYSQL_CONSTRAINT_URL \
            -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR \
            -sd $KNP_STORAGE_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH

Empty MySQL database if it is running

.. code:: bash

        mysql -h $KNP_MYSQL_HOST -u $KNP_MYSQL_USER -p$KNP_MYSQL_PASS \
                -P $KNP_MYSQL_PORT --execute "drop database KnowNet;"


Redis setup
-----------

Start Redis database if it is not running

.. code:: bash

        python3 code/redis_utilities.py \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
            -rd $KNP_REDIS_DIR -rps $KNP_REDIS_PASS -rcu $KNP_REDIS_CONSTRAINT_URL\
            -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH

Empty Redis database if it is running

.. code:: bash

        redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
        redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS BGREWRITEAOF

nginx setup
-----------

Build the documentation

.. code:: bash

        cd $KNP_WORKING_DIR/KnowNet_Pipeline/docs/
        make html
        cd $KNP_WORKING_DIR/KnowNet_Pipeline

Start nginx server if it is not running

.. code:: bash

        mkdir $KNP_NGINX_DIR
        mkdir $KNP_NGINX_DIR/data/
        mkdir $KNP_NGINX_DIR/docs/
        python3 code/nginx_utilities.py \
            -ngp $KNP_NGINX_PORT -ncu $KNP_NGINX_CONSTRAINT_URL \
            -ngd $KNP_NGINX_DIR -ngcf $KNP_NGINX_CONF \
            -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH


Clear the chronos queue
-----------------------

.. code:: bash

        for c in $KNP_CHRONOS_URL ; do
            curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep '"name"' | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
            for s in 'export-' 'import-' 'map-' 'table-' 'fetch-' 'check-' 'KN_starter'  ; do
                echo $s
                for i in `grep "$s" /tmp/t.txt  `; do
                    CMD="curl -L -X DELETE $c/scheduler/job/$i";
                    echo "$CMD";
                    eval "$CMD";
                done;
            done;
        done;

Check the status of jobs
------------------------

.. code:: bash

        python3 code/job_status.py -c $KNP_CHRONOS_URL

Run setup pipeline (time: 2hr 30min)
------------------------------------

.. code:: bash

        python3 code/workflow_utilities.py CHECK -su \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES

Run parse pipeline (time: 2hr)
------------------------------

.. code:: bash

        python3 code/workflow_utilities.py CHECK \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR

Run import pipeline (time: 2hr 45min)
-------------------------------------

.. code:: bash

        python3 code/workflow_utilities.py IMPORT \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR

Run export pipeline (time: )
----------------------------

.. code:: bash

        mkdir -p $KNP_EXPORT_DIR
        cp code/mysql/edge_type.txt $KNP_EXPORT_DIR
        
        ## add gene maps
        cp $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map/species/species.txt $KNP_EXPORT_DIR/species.txt
        for TAXON in `cut -f1 $KNP_EXPORT_DIR/species.txt `; do
            echo $TAXON;
            mkdir -p $KNP_EXPORT_DIR/Species/$TAXON;
            mysql -h$KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P$KNP_MYSQL_PORT -D$KNP_MYSQL_DB -e "\
                SELECT ns.node_id \
                FROM node_species ns \
                WHERE ns.taxon = $TAXON \
                ORDER BY ns.node_id" \
                | tail -n +2 > $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
                LANG=C.UTF-8 python3 code/conv_utilities.py -mo LIST \
                    -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT -t $TAXON \
                    $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
                rm $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
        done
        
        ## add subnetworks
        mysql -h$KNP_MYSQL_HOST -p$KNP_MYSQL_PASS -u$KNP_MYSQL_USER -P$KNP_MYSQL_PORT -DKnowNet -e "\
           SELECT et.n1_type, ns2.taxon, e.et_name, count(1) \
           FROM edge e, edge_type et, node_species ns2 \
           WHERE e.et_name=et.et_name \
           AND e.n2_id=ns2.node_id \
           GROUP BY et.n1_type, ns2.taxon, e.et_name" \
           > $KNP_EXPORT_DIR/db_contents.txt
        head -n1 $KNP_EXPORT_DIR/db_contents.txt \
            > $KNP_EXPORT_DIR/directories.txt
        awk -v x=125000 '$4 >= x' $KNP_EXPORT_DIR/db_contents.txt \
            | grep "^Gene" >> $KNP_EXPORT_DIR/directories.txt
        awk -v x=4000 '$4 >= x' $KNP_EXPORT_DIR/db_contents.txt \
            | grep "^Property" >> $KNP_EXPORT_DIR/directories.txt
        python3 code/workflow_utilities.py EXPORT \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL -b $KNP_EXPORT_DIR \
            -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES \
            -p "$(tail -n+2 $KNP_EXPORT_DIR/directories.txt \
                | cut -f2,3 \
                | sed -e 's/\t/::/g' \
                | sed -e ':a;N;$!ba;s/\n/,,/g')"
        
        ## extract Property node maps
        for CLASS1 in Property; do
            for line in `grep $CLASS1 $KNP_EXPORT_DIR/directories.txt | sed 's#\t#/#g'` ; do
                echo $line;
                CLASS=$(echo $line | cut -f1 -d/)
                TAXON=$(echo $line | cut -f2 -d/)
                ETYPE=$(echo $line | cut -f3 -d/)
                grep Property $KNP_EXPORT_DIR/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.node_map > $KNP_EXPORT_DIR/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.pnode_map
            done
        done;

Check for errors
----------------

.. code:: bash

        grep -ri -e failed -e error -e killed ../logs_*

Export databases
----------------

.. code:: bash

        mysqldump -h $KNP_MYSQL_HOST -u $KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT $KNP_MYSQL_DB | gzip > $KNP_S3_DIR/mysql.gz
        redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS SAVE && mv $KNP_REDIS_DIR/dump.rdb $KNP_S3_DIR/dump.rdb

Import databases
----------------

.. code:: bash

        mysql -h $KNP_MYSQL_HOST -u $KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT -e "CREATE DATABASE KnowNet;"
        gzip -dc $KNP_S3_DIR/mysql.gz | mysql -h $KNP_MYSQL_HOST -u $KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P $KNP_MYSQL_PORT KnowNet

Set up your AWS credentials (modify with your keys)
---------------------------------------------------

.. code:: bash

        mkdir ~/.aws
        echo -e "[default]\naws_access_key_id = ABC\naws_secret_access_key = XYZ" > ~/.aws/credentials

Setup and delete AWS RDS/EC instance
---------------------------------

.. code:: bash

        aws rds create-db-instance \
                --db-instance-class db.m4.2xlarge \
                --allocated-storage 800 \
                --db-instance-identifier knownet \
                --master-username p1user \
                --master-user-password knowdev249 \
                --port 3306 \
                --engine mysql \
                --engine-version 5.6.27 \
                --vpc-security-group-ids sg-03700267 \
                --db-subnet-group-name default \
                --backup-retention-period 0 \
                --no-multi-az \
                --auto-minor-version-upgrade \
                --license-model general-public-license \
                --publicly-accessible \
                --storage-type gp2 \
                --no-storage-encrypted \
                --no-copy-tags-to-snapshot \
                --monitoring-interval 0 \
                --no-enable-iam-database-authentication
        aws rds delete-db-instance \
                --db-instance-identifier knownet \
                --skip-final-snapshot

        aws elasticache create-cache-cluster \
                --cache-node-type cache.m4.xlarge \
                --cache-cluster-id knowredis1706 \
                --snapshot-arns arn:aws:s3:::KnowNets/KN-20rep-1706/redis-KN-20rep-1706/dump.rdb \
                --port 6381 \
                --az-mode single-az \
                --preferred-availability-zone us-west-2a \
                --num-cache-nodes 1 \
                --engine redis \
                --engine-version 3.2.4 \
                --cache-subnet-group-name default \
                --auto-minor-version-upgrade \
                --security-group-ids sg-39b2f842   


Copy directory to S3 bucket
---------------------------

.. code:: bash

        pip install awscli
        aws s3 sync $KNP_WORKING_DIR/$KNP_BUCKET s3://$KNP_BUCKET

Create report of results
------------------------

.. code:: bash

        cp -r $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map $KNP_STORAGE_DIR/$KNP_DATA_PATH/id_map
        code/reports/enumerate_files.sh $KNP_STORAGE_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
            $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
        git add -f tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
        git commit -m 'adding result report'
        git push
