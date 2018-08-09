Step By Step KN Build
*********************

This section contains instruction if you wish to run each step of the Knowledge Network
Build Pipeline separately.  It makes heavy use of the environmental variables specified 
at the beginning.

Set environment variables
-------------------------

.. code:: bash

        KNP_CHRONOS_URL='127.0.0.1:8888'
        KNP_BUILD_NAME='hsap-all'
        KNP_CODE_DIR="/kn_builder/code/"
        KNP_WORKING_DIR='./'
        KNP_STORAGE_DIR="$KNP_WORKING_DIR"
        KNP_DB_DIR="$KNP_WORKING_DIR"
        KNP_DATA_PATH='kn-data-'$KNP_BUILD_NAME
        KNP_LOGS_PATH='kn-logs-'$KNP_BUILD_NAME
        KNP_ENS_SPECIES='homo_sapiens'
        
        KNP_EXPORT_DIR="$KNP_WORKING_DIR/kn-final-$KNP_BUILD_NAME"
        KNP_MARATHON_URL='127.0.0.1:8080/v2/apps'
        
        export KNP_MYSQL_HOST='127.0.0.1'
        export KNP_MYSQL_PORT='3306'
        export KNP_MYSQL_PASS='KnowEnG'
        export KNP_MYSQL_USER='root'
        export KNP_MYSQL_DB='KnowNet'
        KNP_MYSQL_DIR=$KNP_DB_DIR'/kn-mysql-'$KNP_MYSQL_PORT'-'$KNP_BUILD_NAME
        KNP_MYSQL_CONF='build_conf/'
        KNP_MYSQL_MEM='10000'
        KNP_MYSQL_CPU='0.5'
        KNP_MYSQL_CONSTRAINT_URL='127.0.0.1'
        
        export KNP_REDIS_HOST='127.0.0.1'
        export KNP_REDIS_PORT='6379'
        export KNP_REDIS_PASS='KnowEnG'
        KNP_REDIS_DIR=$KNP_DB_DIR'/kn-redis-'$KNP_REDIS_PORT'-'$KNP_BUILD_NAME
        KNP_REDIS_MEM='8000'
        KNP_REDIS_CPU='0.5'
        KNP_REDIS_CONSTRAINT_URL='127.0.0.1'
        

Copy pipeline code
------------------

.. code:: bash

        cd "$KNP_CODE_DIR"
        git clone https://github.com/KnowEnG/KN_Builder.git
        cd KN_Builder/

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

        python3 src/code/mysql_utilities.py \
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

        python3 src/code/redis_utilities.py \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -rm $KNP_REDIS_MEM -rc $KNP_REDIS_CPU \
            -rd $KNP_REDIS_DIR -rps $KNP_REDIS_PASS -rcu $KNP_REDIS_CONSTRAINT_URL\
            -m $KNP_MARATHON_URL -wd $KNP_WORKING_DIR -lp $KNP_LOGS_PATH

Empty Redis database if it is running

.. code:: bash

        redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS FLUSHDB
        redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS BGREWRITEAOF


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

        python3 src/code/job_status.py -c $KNP_CHRONOS_URL

Run setup pipeline (time: 2hr 30min)
------------------------------------

.. code:: bash

        python3 src/code/workflow_utilities.py CHECK -su \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR -es $KNP_ENS_SPECIES

Run parse pipeline (time: 2hr)
------------------------------

.. code:: bash

        python3 src/code/workflow_utilities.py CHECK \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR

Run import pipeline (time: 2hr 45min)
-------------------------------------

.. code:: bash

        python3 src/code/workflow_utilities.py IMPORT \
            -myh $KNP_MYSQL_HOST -myp $KNP_MYSQL_PORT \
            -myps $KNP_MYSQL_PASS -myu $KNP_MYSQL_USER \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT \
            -wd $KNP_WORKING_DIR -dp $KNP_DATA_PATH -lp $KNP_LOGS_PATH \
            -c $KNP_CHRONOS_URL \
            -sd $KNP_STORAGE_DIR

Run export pipeline (time: 45 mins)
-----------------------------------

.. code:: bash

        src/code/export1.sh
        src/code/export2.sh

Check for errors
----------------

.. code:: bash

        grep -ri -e failed -e error -e killed $KNP_LOGS_PATH/*

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

Create report of results
------------------------

.. code:: bash

        cp -r $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map $KNP_STORAGE_DIR/$KNP_DATA_PATH/id_map
        src/code/reports/enumerate_files.sh $KNP_STORAGE_DIR/$KNP_DATA_PATH COUNTS $KNP_MYSQL_HOST \
            $KNP_REDIS_HOST $KNP_MYSQL_PORT $KNP_REDIS_PORT > tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
        git add -f tests/KN03-KClus-build.$KNP_DATA_PATH.pipe
        git commit -m 'adding result report'
        git push

