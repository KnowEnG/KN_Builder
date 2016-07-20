.. _formats-ref:

KnowNet Pipeline Data Formats
*****************************

.. _file-metadata-label:

file_metadata (produced by check_utilities and updated by fetch_utilities)
-------------
::

    'alias' (str):              The alias name,
    'alias_info' (str):         A short string with information
                                about the alias,
    'checksum' (str):           Checksum of the downloaded file,
    'dependencies' (list):      List of other aliases that the alias
                                depends on,
    'fetch_needed' (bool):      True if file needs to be downloaded
                                from remote source. A fetch will
                                be needed if the local file does
                                not exist, or if the local and
                                remote files have different date
                                modified or file sizes,
    'file_exists' (bool):       Boolean representing if file is
                                already present on local disk,
    'is_map' (bool):            Boolean representing if alias is used for
                                source specific mapping of nodes or edges,
    'line_count' (int):         Line count of the downloaded file,
    'local_file_name' (str):    Name of the downloaded file on local disk,
    'num_chunks' (int):         Number of raw_line chunks downloaded
                                file is split into,
    'remote_date' (float):      Modification date of file on the remote
                                source,
    'remote_file' (str):        File to extract if remote file
                                location is a directory,
    'remote_size' (int):        Size of file on the remote source,
    'remote_url' (str):         Url of file on the remote source,
    'remote_version' (str):     Release version of the remote source,
    'source' (str):             The source name.

rawline (produced by fetch_utilities)
-------
::
    'line_hash' (str):      md5 checksum of rawline field
    'line num' (int):       line number in downloaded file
    'file_id' (str):        processed name of downloaded file
    'rawline' (str):        original line string from downloaded source

table (produced by table_utilities)
----
::

    'line_chksum' (int):    checksum of original line string from source
    'n1name' (str):         node1 name to map from original source
    'n1hint' (str):         suggestion of node1 name type to aid mapping
    'n1type' (str):         type of node1: 'gene', 'property'
    'n1spec' (int):         taxon id of node1 species, 0 if property, 
                            'unknown' otherwise
    'n2name' (str):         node2 name to map from original source
    'n2hint' (str):         suggestion of node2 name type to aid mapping
    'n2type' (str):         type of node2: 'gene', 'property'
    'n2spec' (int):         taxon id of node2 species, 0 if property, 
                            'unknown' otherwise
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

status
----
::

    'table_hash' (str):     md5 checksum of original line string from source
    'n1name' (str):         node1 name to map from original source
    'n1hint' (str):         suggestion of node1 name type to aid mapping
    'n1type' (str):         type of node1: 'gene', 'property'
    'n1spec' (int):         taxon id of node1 species, 0 if property, 
                            'unknown' otherwise
    'n2name' (str):         node2 name to map from original source
    'n2hint' (str):         suggestion of node2 name type to aid mapping
    'n2type' (str):         type of node2: 'gene', 'property'
    'n2spec' (int):         taxon id of node2 species, 0 if property, 
                            'unknown' otherwise
    'et_hint' (str):        name / hint of edge type
    'score' (float):        score for edge
    'edge_chksum' (int):    checksum of raw edge generated from source line
