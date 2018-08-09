.. _adv-params-ref:

.. highlight:: none


Advanced Parameters
*******************

There are many additional parameters that may be specified when running the 
primary build_status.py script.

.. code::

    usage: build_status.py [-h] [-c CHRONOS] [-m MARATHON] [-i BUILD_IMAGE]
                           [-es ENS_SPECIES] [-srcs SRC_CLASSES] [-ff] [-tm]
                           [-wd WORKING_DIR] [-cp CODE_PATH] [-sd [STORAGE_DIR]]
                           [-dp DATA_PATH] [-lp LOGS_PATH] [-ep EXPORT_PATH]
                           [-sp SRC_PATH] [-myh MYSQL_HOST] [-myp MYSQL_PORT]
                           [-myd MYSQL_DIR] [-mym MYSQL_MEM] [-myc MYSQL_CPU]
                           [-mycf MYSQL_CONF] [-myu MYSQL_USER] [-myps MYSQL_PASS]
                           [-rh REDIS_HOST] [-rp REDIS_PORT] [-rd REDIS_DIR]
                           [-rm REDIS_MEM] [-rc REDIS_CPU] [-rps REDIS_PASS]

As a developer, you may modified the src/ code and/or build your own kn_builder 
Docker image. To test your your development code, use a command like this:

.. code::
    
    python3 $MYCODEDIR/src/code/build_status.py \
        -i $MYIMAGE:latest \
        -cp $MYCODEDIR/src/code \
        -es drosophila_melanogaster \
        -srcs kegg,,blast

The parameters can be grouped into four different categories.

Run arguments
-------------
::

    --chronos CHRONOS           url of chronos scheduler or LOCAL or DOCKER
    --marathon MARATHON         url of marathon scheduler
    --build_image BUILD_IMAGE   docker image name to use for kn_build 
                                pipeline
    --ens_species ENS_SPECIES   ,, separated list of ensembl species to run 
                                in setup pipeline
    --src_classes SRC_CLASSES   ,, separated list of source keywords to run 
                                in parse pipeline
    --force_fetch               fetch even if file exists and has not  
                                changed from last run
    --test_mode                 run in test mode by only printing commands

Path arguments
--------------
::

    --working_dir WORKING_DIR   absolute path to toplevel working directory
    --code_path CODE_PATH       absolute path of code directory
    --storage_dir [STORAGE_DIR] name of toplevel directory of storage  
                                directory
    --data_path DATA_PATH       relative path of data directory from  
                                toplevel
    --logs_path LOGS_PATH       relative path of data directory from  
                                toplevel
    --export_path EXPORT_PATH   relative path of export directory from  
                                toplevel
    --src_path SRC_PATH         relative path of srcClass directory from  
                                code_path

MySQL arguments
---------------
::

    --mysql_host MYSQL_HOST     address of mySQL db
    --mysql_port MYSQL_PORT     port for mySQL db
    --mysql_dir MYSQL_DIR       absolute directory for MySQL db files
    --mysql_mem MYSQL_MEM       memory for deploying MySQL container
    --mysql_cpu MYSQL_CPU       cpus for deploying MySQL container
    --mysql_conf MYSQL_CONF     config directory for deploying MySQL  
                                container
    --mysql_user MYSQL_USER     user for mySQL db
    --mysql_pass MYSQL_PASS     password for mySQL db

Redis arguments
---------------
::

    --redis_host REDIS_HOST     address of Redis db
    --redis_port REDIS_PORT     port for Redis db
    --redis_dir REDIS_DIR       absolute directory for Redis db files
    --redis_mem REDIS_MEM       memory for deploying redis container
    --redis_cpu REDIS_CPU       cpus for deploying redis container
    --redis_pass REDIS_PASS     password for Redis db

