Requirements
============

0) System requirements:
    a) Need 4cpu, 16GB RAM machine, recommend 2TB disk
    b) No Mesos/Zookeeper/Chronos/Marathon Running
1) make
2) Docker
3) Docker Compose: https://docs.docker.com/compose/install/#install-compose

Quick Run
=========

First, check out this repo:

.. code::

    git clone https://github.com/KnowEnG/KnowNet_Pipeline_Tools
    cd KnowNet_Pipeline_Tools

.. note:: Depending on your setup, some of the following commands may require root.  This is because docker by default does not allow nonroot processes to start jobs.  In addition, the jobs are run as root inside docker, so all the output and intermediate files will be created as root.

Then, running the pipeline is as simple as running :code:`make`.

.. code::

    make knownet

This will start up our mesos environment, and then run the pipeline for all officially supported species and sources.

Overview of Build Pipeline
==========================

The make command will produce a large amount of output.  First it will show the status of starting up mesos and chronos, and then starting up the databases.  After it finishes with that, it will start the processing pipeline, and periodically print the status of the pipeline.  It should return when either an error occurs or the pipeline finishes running.

Output Files
------------

Running the pipeline will create several directories:

=========================================   ==========
Contents                                    Directory	
=========================================   ==========	
Stores the redis database.                  kn-redis	
Stores the downloaded and processed data.   kn-rawdata	
Stores the MySQL database.                  kn-mysql	
Stores the log files.                       kn-logs	
Stores the final processed output files.    kn-final	
=========================================   ==========

Information about the output and intermediate file and database formats can be found :ref:`here <formats-ref>`.

Cleaning
========

To clean up the files (except :code:`kn-logs` and :code:`kn-final`), as well as chronos, marathon, and mesos, run:

.. code::

    make clean
    make destroy

Parameters
==========

To specify a list of species or sources, you can specify them as :code:`,,`-separated variables, like so:

.. code::

    make knownet SPECIES=homo_sapiens,,mus_musculus SOURCES=kegg,,stringdb

Resources
=========

Troubleshooting
===============
