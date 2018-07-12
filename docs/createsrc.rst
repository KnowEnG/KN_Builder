Creating a new SrcClass
***********************

Writing the Class
=================

TODO: which directory?
The easiest way to create a new SrcClass is by modifying an existing one to suit your needs.  If there is already a source that has the same or similar format as the one you are trying to add, you can start with that.  This will mean that you have a good starting point for the :code:`table()` method, which is the most complex part of each srcClass.

The :code:`__init__()` Method
-----------------------------

To begin, you will need to modify :code:`__init__()` method to initialize the some attributes that describe metadata about the source, making sure to call :code:`__init__()` of the superclass:

.. container:: toggle

    .. container:: header

        **SrcClass**

    .. autoclass:: check_utilities.SrcClass
        :noindex:

Other Methods
-------------

You will then need to override or modify the other methods of SrcClass if the existing ones do not work for your new source.  The most important methods are:

.. container:: toggle

    .. container:: header

        table

    .. automethod:: check_utilities.SrcClass.table

.. container:: toggle

    .. container:: header

        get_remote_url

    .. automethod:: check_utilities.SrcClass.get_remote_url

.. container:: toggle

    .. container:: header

        get_source_version

    .. automethod:: check_utilities.SrcClass.get_source_version

.. container:: toggle

    .. container:: header

        get_aliases

    .. automethod:: check_utilities.SrcClass.get_aliases

Most of the time the defaults can be used for the other methods of the SrcClass subclass.

Testing and Running the Class
=============================

If you want to run the code using docker (the official method), you can build a local docker image that includes your code:

.. code::

        docker build path/to/KN_Builder/src/ -t knoweng/kn_builder:latest

If you do so, remember to remove the image before trying to run the official release again.

You can then run the pipeline as normal, making sure to specify your source in the arguments:

.. code::

        cd path/to/Knownet_Pipeline_Tools/
        make SOURCES=<source>
