Advanced Troubleshooting
========================

1) List all Mesos tasks

.. code::

    curl -L -X GET 127.0.0.1:5050/tasks
    curl -L -X GET 127.0.0.1:5050/system/stats.json
    curl -L -X GET 127.0.0.1:5050/metrics/snapshot
    curl -L -X GET 127.0.0.1:5050/master/slaves

2) List all Marathon job statuses

.. code::

    curl -X GET 127.0.0.1:8080/v2/apps/

3) List all Chronos jobs

.. code::

    curl -L -X GET 127.0.0.1:8888/scheduler/jobs

4) Get statuses of all Chronos job that are not successes

.. code::

    curl -L -s -X GET 127.0.0.1:8888/scheduler/graph/csv | grep node, | \
        awk -F, '{print $3"\t"$4"\t"$1"\t"$2}' | sort | uniq | grep -v success

5) Remove all stopped Docker containers

.. code::

    docker ps -aq --no-trunc | xargs docker rm

6) Get Docker container usage stats

.. code::

    eval "docker inspect --format='{{.Name}}' \$(docker ps -aq --no-trunc) | \
      cut -c 2- | xargs docker stats --no-stream=true"

7) Find Mesos identifiers per pipeline stage

.. code::

    for i in mysqld redis-server check_utilities fetch_utilities table_utilities conv_utilities import_utilities export_utilities KN_starter next_step; do
      echo $i
      docker ps -a --no-trunc | grep $i | rev | cut -d' ' -f 1 | rev | awk -v LABEL="$i" '{print $1"\t"LABEL}'
    done;
