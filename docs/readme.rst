System Requirements
===================

The run the Knowledge Network Build Pipeline with the KN_Builder, you must have three tools installed:
    1) make
    2) Docker
    3) Docker Compose: https://docs.docker.com/compose/install/#install-compose

Your system must also meet the following requirements:
    a) Minimum of 4 CPUs, 16GB RAM, 2TB disk
    b) Must mot have Mesos/Zookeeper/Chronos/Marathon running at default ports

Quick Start
===========

First, check out the quick run repo:

.. code::

    git clone https://github.com/KnowEnG/KnowNet_Pipeline_Tools
    cd KnowNet_Pipeline_Tools

.. note:: Depending on your setup, some of the following commands may require root. This is because docker by default does not allow nonroot processes to start jobs.  In addition, the jobs are run as root inside docker, so all the output and intermediate files will be created as root.

Then, running the pipeline is as simple as running :code:`make`:

.. code::

    make knownet

This will start up our Mesos environment and then run the build pipeline for all officially
supported species and sources.

Overview of Build Pipeline
==========================

The make command will produce a large amount of output.  First, it will show the status
of starting up Mesos and Chronos and then show starting up the databases.  After it finishes
that phase, it will start the build pipeline and periodically print the status of the
pipeline.  It should return when either an error occurs or the pipeline finishes running.

The build pipeline consists of several stages:

1) SETUP: Downloads and imports Ensembl and sets up gene mapping information.
2) CHECK: Downloads and processes the rest of the sources.  This consists of several substeps.
    a) fetch: Downloads the source data files.
    b) table: Takes the source files and reformats it into our table file format.
    c) map: Maps the identifiers in the source to our internal identifiers.
3) IMPORT: Imports all of the files into mysql and redis databases.
4) EXPORT: Exports the Knowledge Network into flatfiles and dumps the mysql and redis databases.

Output Files
------------

Running the pipeline will create several directories:

==========   =========================================
Directory    Contents
==========   =========================================
kn-final     Stores the final processed output files.
kn-logs      Stores the log files.
kn-rawdata   Stores the downloaded and processed data.
kn-mysql     Stores the MySQL database.
kn-redis     Stores the redis database.
==========   =========================================

Information about the output and intermediate file and database formats can be found :ref:`here <formats-ref>`.

Clean Up After Build
====================

To clean up the files (except :code:`kn-logs` and :code:`kn-final`), as well as Chronos, Marathon, and Mesos, run:

.. code::

    make clean
    make destroy

Primary Parameters
==================

To build the Knowledge Network for only a subset of species or sources, you can specify them as :code:`,,`-separated variables, like so:

.. code::

    make knownet SPECIES=homo_sapiens,,mus_musculus SOURCES=kegg,,stringdb

The names of the SPECIES should be all lowercase and spaces replaced by underscores.

The possible SOURCES names can be found here: SrcClasses_

Additional Resources
====================

1) Summary_ of Current Knowledge Network Contents.
2) Details_ of Current Knowledge Network Contents.
3) List of Related Knowledge Network Tools_.

.. _Summary: https://knoweng.org/kn-overview/
.. _Details: https://knoweng.org/kn-data-references/
.. _Tools: https://knoweng.org/kn-tools/
.. _SrcClasses: https://github.com/KnowEnG/KN_Builder/tree/master/src/code/srcClass


Basic Troubleshooting
=====================

If you run into errors when building the Knowledge Network, you can look at the status of 
all remaining jobs on Chronos

.. code::

    curl -L -s -X GET 127.0.0.1:8888/scheduler/graph/csv | grep node, | \
      awk -F, '{print $3"\t"$4"\t"$1"\t"$2}' | sort | uniq | grep -v succ
      
For any failed job (e.g. JOBNAME), you can look to 
    1) the original Chronos command at: kn-logs/chronos_jobs/JOBNAME.json or 
    2) the captured output log at: kn-logs/JOBNAME.json.  

These may provide you with a reason that the job is failing.  If the original source has changed 
their format, you may rerun using the SOURCES parameter, specifying all sources except the 
problematic ones.

