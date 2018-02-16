

KN_Builder
----------

Fetch and parse source files to construct the KnowEnG Knowledge Network


Running Manually
================

1. Enter the docker container::

    docker run -it -w='/home/ubuntu' -v `pwd`:/home/ubuntu cblatti3/kn_builder:latest

2. run command within the docker container::

    python3 /kn_builder/job_status.py \
      --species homo_sapiens \
      --source stringdb reactome enrichr biogrid \
      --build_name hsap-1802


