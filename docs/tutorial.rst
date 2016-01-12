.. _tutorial-ref:

KnowNet Pipeline Tutorial
*************************

Running Locally
---------------

Set environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~
::

    KNP_LOCAL_DIR='/workspace/apps/KnowNet_Pipeline'
    KNP_CLOUD_DIR='/storage-pool/blatti/KnowNet_Pipeline/'
    KNP_DATA_PATH='data_pipe'
    KNP_MYSQL_HOST='knowcharles.dyndns.org'
    KNP_REDIS_HOST='knowcharles.dyndns.org'
    KNP_CHRONOS_URL='mmaster01.cse.illinois.edu:4400'
    KNP_SRC='dip'
    KNP_ALIAS='PPI'
    KNP_CHUNK='1'

Running single step locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~
1.  check for updates (:py:mod:`check_utilities`) to remote file for source
    named $KNP_SRC (e.g. 'dip')

  * updates :ref:`file-metadata-label` `file_metadata.json <formats.html#file_metadata>`_ and mysql

::

    KNP_CMD="python3 code/check_utilities.py $KNP_SRC -dp $KNP_DATA_PATH \
                -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST"
    echo $KNP_CMD

2.  fetch remote files (:py:mod:`fetch_utilities`) for alias named
    $KNP_ALIAS (e.g. 'PPI') of source $KNP_SRC

  * for ontology files, extracts mapping dictionary and imports into redis,
    extracts nodes and node_metadata and imports into mysql, updates
    file_metadata json and mysql
  * for data files, creates .rawline. chunks and imports to mysql, updates
    file_metadata json and mysql
  * for ensembl, imports mysql database, extracts gene mappings into redis,
    imports nodes into mysql, updates file_metadata json and mysql

::

    cd $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS
    KNP_CMD="python3 ../../../code/fetch_utilities.py file_metadata.json \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

3.  table (:py:mod:`table_utilities`) for chunk KNP_CHUNK (e.g '1') of alias
    named $KNP_ALIAS of source $KNP_SRC

  * converts .rawline. file into 11 column description .edge. file to prepare
    edges for entity mapping, also created edge and node metadata files as
    necessary and sort, uniques them

::

    cd $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS
    KNP_CMD="python3 ../../../code/table_utilities.py \
        chunks/$KNP_SRC.$KNP_ALIAS.rawfile.$KNP_CHUNK.txt file_metadata.json \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR"
    echo $KNP_CMD

4.  entity mapping (:py:mod:`conv_utilities`) and implicit import
    (:py:mod:`import_utilities`) for chunk CHUNK of alias named $KNP_ALIAS of
    source $KNP_SRC

  * converts .edge. file into 6 column description .conv. file and .status.
    file using redis, sorts and uniques .conv. and .edge2line., and inserts
    .conv., .node_meta., .edge_meta., and .edge2line. file into mysql

::

    KNP_CMD="python3 code/conv_utilities.py \
        $KNP_DATA_PATH/$KNP_SRC/$KNP_ALIAS/chunks/$KNP_SRC.$KNP_ALIAS.edge.$KNP_CHUNK.txt \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

Running multiple steps locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  setup databases and entity mapping

  * may first want to clear out mysql and clear out redis

::

    KNP_CMD="mysql -h $KNP_MYSQL_HOST --port 3306 -uroot -pKnowEnG KnowNet \
        --execute \"drop database KnowNet;\""
    echo $KNP_CMD

    KNP_CMD="redis-cli -h $KNP_REDIS_HOST -a KnowEnG FLUSHDB"
    echo $KNP_CMD

setup locally
^^^^^^^^^^^^^

2.  check all setup remote sources for updates (:py:mod:`setup_utilities`)

  * updates file_metadata json and mysql

::

    KNP_CMD="python3 code/setup_utilities.py CHECK LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

3.  fetch all updated setup files from remote sources, process ontologies and
    databases (:py:mod:`setup_utilities`)

::

    KNP_CMD="python3 code/setup_utilities.py FETCH LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

4.  run full setup pipeline (:py:mod:`setup_utilities`) without redoing
    ensembl (in place of Step 2 and 3), *takes about 36 minutes*

::

    KNP_CMD="python3 code/setup_utilities.py CHECK LOCAL PIPELINE \
        -dp $KNP_DATA_PATH -ne -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

pipeline locally
^^^^^^^^^^^^^^^^

5.  check for all pipeline remote sources updates (:py:mod:`pipeline_utilities`)

::

    KNP_CMD="python3 code/pipeline_utilities.py CHECK LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST"
    echo $KNP_CMD

6.  fetch updated files from remote sources, process ontologies
    (:py:mod:`pipeline_utilities`)

::

    KNP_CMD="python3 code/pipeline_utilities.py FETCH LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

7.  'table' raw files to standard table format (:py:mod:`pipeline_utilities`)

::

    KNP_CMD="python3 code/pipeline_utilities.py TABLE LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR"
    echo $KNP_CMD

8.  map entries to KN entities and produce edges and metadata files
    (:py:mod:`pipeline_utilities`)

::

    KNP_CMD="python3 code/pipeline_utilities.py MAP LOCAL STEP \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

9.  run full sources pipeline (:py:mod:`pipeline_utilities`) (in place of 5, 6,
    7, and 8), *takes about about 45 minutes*

::

    KNP_CMD="python3 code/pipeline_utilities.py CHECK LOCAL PIPELINE \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST"
    echo $KNP_CMD

Running On Cloud
----------------

running all steps in cloud mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  setup cloud pipeline (:py:mod:`setup_utilities`) *takes about 22 minutes*

::

    KNP_CMD="python3 code/setup_utilities.py CHECK CLOUD PIPELINE \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR"
    echo $KNP_CMD

2.  pipeline cloud pipeline (:py:mod:`pipeline_utilities`) *takes about 24
    minutes*

::

    KNP_CMD="python3 code/pipeline_utilities.py CHECK CLOUD PIPELINE \
        -dp $KNP_DATA_PATH -ld $KNP_LOCAL_DIR -myh $KNP_MYSQL_HOST \
        -rh $KNP_REDIS_HOST -c $KNP_CHRONOS_URL -cd $KNP_CLOUD_DIR"
    echo $KNP_CMD

running one full step in cloud mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  setup cloud all fetch (:py:mod:`setup_utilities`)

::

    for i in ensembl ppi species; do
    echo $i
    python3 code/setup_utilities.py FETCH CLOUD STEP -dp cloud_pipe -p $i \
        -ld /workspace/prototype/KnowNet_Pipeline/ \
        -rh knowcharles.dyndns.org -myh knowcharles.dyndns.org \
        -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/ \
    ; done;

2.  pipeline cloud all fetch (:py:mod:`pipeline_utilities`)

::

    for i in `ls code/srcClass/*py | sed 's#code/srcClass/##g' | sed 's#.py##g'`;
        do echo $i;
        python3 code/pipeline_utilities.py FETCH CLOUD STEP \
        -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ \
        -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe \
        -rh knowice.cs.illinois.edu -rp 6380 -p $i;
    done;

3.  pipeline cloud all table (:py:mod:`pipeline_utilities`)

::

    for i in `ls -d cloud_pipe/*/*/chunks | sed 's#cloud_pipe/##g' | \
        sed 's#/chunks##g' | sed 's#/#,#g'  `;
        do echo $i;
        python3 code/pipeline_utilities.py TABLE CLOUD STEP \
        -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ \
        -ld /workspace/prototype/P1_source_check/ -rh knowice.cs.illinois.edu -rp 6380 \
        -p $i -dp cloud_pipe;
    done;

4.  pipeline cloud all conv (:py:mod:`pipeline_utilities`)

::

    for i in `ls cloud_pipe/*/*/chunks/*.edge.* | sed 's#cloud_pipe/##g' | sed 's#/chunks##g' | sed 's#/#\t#g' | cut -f3  `; do echo $i; python3 code/pipeline_utilities.py MAP CLOUD STEP -c mmaster01.cse.illinois.edu:4400 -cd /storage-pool/blatti/P1_source_check/ -ld /workspace/prototype/P1_source_check/ -dp cloud_pipe -rh knowice.cs.illinois.edu -rp 6380 -p $i; done

cloud cleanup
~~~~~~~~~~~~~

1.  when complete, be a good citizen and remove jobs from the cloud

::

    for i in `ls code/chron_jobs/*json | sed "s#code/chron_jobs/##g" | sed "s/.json//g"` ; do CMD="curl -L -X DELETE mmaster01.cse.illinois.edu:4400/scheduler/job/$i"; echo "$CMD"; eval $CMD; done


2.  delete ALL P1 jobs on prototype cloud - USE CAREFULLY

::

    for c in 'mmaster01.cse.illinois.edu:4400' 'knowmaster.dyndns.org:4400'; do
        curl -L -X GET $c/scheduler/jobs | sed 's#,#\n#g' | sed 's#\[##g' | grep name | sed 's#{"name":"##g' | sed 's#"##g' > /tmp/t.txt
        for s in 'check-' 'fetch-' 'table-' 'conv-'; do
            echo $s
            for i in `grep "$s" /tmp/t.txt  `; do
                CMD="curl -L -X DELETE $c/scheduler/job/$i";
                echo "$CMD";
                eval "$CMD";
            done;
        done;
    done;

Checks and Reports
------------------

1. quick check for completeness

::

    code/reports/enumerate_files.sh local_pipe/ COUNTS




