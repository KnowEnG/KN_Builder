.. _formats-ref:

KnowNet Pipeline Data Formats
*****************************

.. _file-metadata-label:

file_metadata (produced by check_utilities and updated by fetch_utilities)
--------------------------------------------------------------------------
::

    'alias' (str):              the alias name
    'alias_info' (str):         a short string with information
                                about the alias
    'checksum' (str):           md5 checksum of the downloaded file
    'dependencies' (list):      list of other aliases that the alias
                                depends on
    'fetch_needed' (bool):      True if file needs to be downloaded
                                from remote source. A fetch will
                                be needed if the local file does
                                not exist, or if the local and
                                remote files have different date
                                modified or file sizes
    'file_exists' (bool):       boolean representing if file is
                                already present on local disk
    'is_map' (bool):            boolean representing if alias is used for
                                source specific mapping of nodes or edges
    'line_count' (int):         line count of the downloaded file
    'local_file_name' (str):    name of the downloaded file on local disk
    'num_chunks' (int):         number of raw_line chunks downloaded
                                file is split into
    'remote_date' (float):      modification date of file on the remote
                                source
    'remote_file' (str):        file to extract if remote file
                                location is a directory
    'remote_size' (int):        size of file on the remote source
    'remote_url' (str):         url of file on the remote source
    'remote_version' (str):     release version of the remote source
    'source' (str):             the source name

rawline (produced by fetch_utilities)
-------------------------------------
::

    'line_hash' (str):  md5 checksum of line_str field
    'line num' (int):   line number in downloaded file
    'file_id' (str):    processed name of downloaded file
    'line_str' (str):   original line string from downloaded source

table (produced by table_utilities)
-----------------------------------
::

    'line_hash' (str):  md5 checksum of original line string from source
    'n1name' (str):     node 1 name to map from original source
    'n1hint' (str):     suggestion of node 1 name type to aid mapping
    'n1type' (str):     type of node 1 ('Gene', 'Property')
    'n1spec' (int):     taxon id of node 1 species, 0 if property, 
                        'unknown' otherwise
    'n2name' (str):     node 2 name to map from original source
    'n2hint' (str):     suggestion of node 2 name type to aid mapping
    'n2type' (str):     type of node 2 ('Gene', 'Property')
    'n2spec' (int):     taxon id of node 2 species, 0 if property, 
                        'unknown' otherwise
    'et_hint' (str):    name / hint of edge type
    'weight' (float):   score for edge
    'table_hash' (str): md5 checksum of raw edge generated from source line

edge_meta (produced by table_utilities)
---------------------------------------
::

    'line_hash' (str):  md5 checksum of original line string from source
    'info_type' (str):  type of metadate: 'reference', 'experiment', etc
    'info_desc' (str):  description string of metadata

node_meta (produced by table_utilities)
---------------------------------------
::

    'node_id' (str):    mapped node identifier
    'info_type' (str):  type of metadata ('alt_alias', 'link', etc)
    'info_desc' (str):  description string of metadata

node (produced by table_utilities)
----------------------------------
::

    'node_id' (str):    node identifier
    'n_alias' (str):    alternate name for node
    'n_type' (str):     type of node ('Gene', 'Property')

edge (produced by conv_utilities)
---------------------------------
::

    'n1_id' (str):      node 1 mapped identifier
    'n2_id' (str):      node 2 mapped identifier
    'et_name' (str):    name edge type
    'weight' (float):   score for edge type
    'edge_hash' (str):  md5 checksum of mapped edge

edge2line (produced by conv_utilities)
--------------------------------------
::

    'edge_hash' (str):  md5 checksum of mapped edge
    'line_hash' (str):  md5 checksum of original line string from source


status (produced by conv_utilities)
-----------------------------------
::

    'table_hash' (str):     md5 checksum of raw edge generated from source line
    'n1_id' (str):          node 1 mapped identifier
    'n2_id' (str):          node 2 mapped identifier
    'et_name' (str):        name edge type
    'weight' (float):       score for edge type
    'edge_hash' (str):      md5 checksum of mapped edge
    'line_hash' (str):      md5 checksum of original line string from source
    'status' (str):         "production" if both nodes mapped and "unmapped" 
                            otherwise
    'status_desc' (str):    description of reason for status label
