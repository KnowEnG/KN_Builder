.. _modules-ref:

KnowNet Pipeline Data Formats
*****************************

.. _file_metadata-label
file_metadata
-------------
::

    'source' (str):                 The source name,
    'alias' (str):                  The alias name,
    'alias_info' (str):             A short string with information
                                    about the alias,
    'is_map' (bool):                See is_map,
    'dependencies' (lists):         See get_dependencies,
    'remote_url' (str):             See get_remote_url,
    'remote_date' (float):          See get_remote_file_modified,
    'remote_version' (str):         See get_source_version,
    'remote_file' (str):            File to extract if remote file
                                    location is a directory,
    'remote_size' (int):            See get_remote_file_size,
    'local_file_name' (str):        See get_local_file_info,
    'local_file_exists' (bool):     See get_local_file_info,
    'fetch_needed' (bool):          True if file needs to be downloaded
                                    from remote source. A fetch will
                                    be needed if the local file does
                                    not exist, or if the local and
                                    remote files have different date
                                    modified or file sizes.

rawline
-------
::

    'file' (str):           processed name of downloaded file
    'line num' (int):       line number in downloaded file
    'line_chksum' (int):    checksum of rawline field
    'rawline' (str):        original line string from downloaded source

edge
----
::

    'line_chksum' (int):    checksum of original line string from source
    'n1name' (str):         node1 name to map from original source
    'n1hint' (str):         suggestion of node1 name type to aid mapping
    'n1type' (str):         type of node1: 'gene', 'property'
    'n1spec' (int):         taxon id of node1 species, 0 if property
    'n2name' (str):         node2 name to map from original source
    'n2hint' (str):         suggestion of node2 name type to aid mapping
    'n2type' (str):         type of node2: 'gene', 'property'
    'n2spec' (int):         taxon id of node2 species, 0 if property
    'et_hint' (str):        name / hint of edge type
    'score' (float):        score for edge
    'edge_chksum' (int):    checksum of raw edge generated from source line

conv
----
::

    'n1id' (str):           node1 mapped identifier
    'n2id' (str):           node2 mapped identifier
    'edge_type' (str):      name edge type
    'score' (float):        score for edge type
    'edge_chksum' (str):    checksum of raw edge that produced mapped edge

edge_meta
---------
::

    'line_chksum' (int):    checksum of original line string from source
    'info_type' (str):      type of metadate: 'reference', 'experiment', etc
    'info_desc' (str):      description string of metadata

node_meta
---------
::

    'n1id' (str):           node1 mapped identifier
    'info_type' (str):      type of metadate: 'alt_alias', 'link', etc
    'info_desc' (str):      description string of metadata