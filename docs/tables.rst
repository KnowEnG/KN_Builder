.. _tables-ref:

KnowNet MySQL TABLE Formats
*****************************
schema
______
:download:`KnowNet Schema <_static/KnowNet_Schema.pdf>`
=======

all_mappings
------------
::

    'dbprimary_acc' varchar(512) DEFAULT NULL:      primary accession number of
                                                    gene from db_name 
    'display_label' varchar(512) DEFAULT NULL:      additional label for gene
                                                    used on Ensembl website
    'db_name' varchar(100) NOT NULL:                name of database where gene
                                                    id is taken from
    'priority' int(11) NOT NULL:                    Ensembl priority placed on
                                                    db_name
    'db_display_name' varchar(255) DEFAULT NULL:    additional label for
                                                    database
    'stable_id' varchar(128) DEFAULT NULL:          Ensembl stable gene id that
                                                    corresponds to the primary
                                                    accession number
    'species' varchar(255) DEFAULT NULL:            species that gene belongs to

edge
----
::

    'n1_id' varchar(64) NOT NULL:       node 1 mapped identifier
    'n2_id' varchar(64) NOT NULL:       node 2 mapped identifier
    'et_name' varchar(80) NOT NULL:     name edge type
    'weight' float NOT NULL:            score for edge type
    'edge_hash' varchar(40) NOT NULL:   md5 checksum of mapped edge
    PRIMARY KEY ('n1_id', 'n2_id', 'et_name')
    KEY 'n2_id' ('n2_id')
    KEY 'et_name' ('et_name')

edge2line
---------
::

    'edge_hash' varchar(40) NOT NULL:   md5 checksum of mapped edge
    'line_hash' varchar(40) NOT NULL:   md5 checksum of original line string
                                        from source
    PRIMARY KEY ('edge_hash', 'line_hash')

edge_meta
---------
::

    'line_hash' varchar(40) NOT NULL:   md5 checksum of original line string
                                        from source
    'info_type' varchar(80) NOT NULL:   type of metadate ('reference', 
                                        'experiment', etc)
    'info_desc' varchar(255) NOT NULL:  description string of metadata
    PRIMARY KEY ('line_hash','info_type','info_desc')

edge_type
---------
::

    'et_name' varchar(80) NOT NULL:     name of edge type
    'n1_type' varchar(12) NOT NULL:     type of node 1 ('Gene', 'Property')
    'n2_type' varchar(12) NOT NULL:     type of node 2 ('Gene', 'Property')
    'bidir' tinyint(1) NOT NULL:        boolean indicating bidirectionality of
                                        edge
    'et_desc' text:                     description of edge type
    'sc_desc' text:                     description of edge score
    'sc_best' float DEFAULT NULL:       highest edge score
    'sc_worst' float DEFAULT NULL:      lowest edge score
    PRIMARY KEY ('et_name')
    KEY ('n1_type')
    KEY ('n2_type')

node
----
::

    'node_id' varchar(64) NOT NULL:         node identifier
    'n_alias' varchar(512) DEFAULT NULL:    alternate name for node
    'n_type' varchar(12) DEFAULT NULL:      type of node ('Gene', 'Property')
    PRIMARY KEY ('node_id')

node_meta
---------
::

    'node_id' varchar(64) NOT NULL:     mapped node identifier
    'info_type' varchar(80) NOT NULL:   type of metadata ('alt_alias', 'link', 
                                        etc)
    'info_desc' varchar(255) NOT NULL:  description string of metadata
    PRIMARY KEY ('node_id','info_type','info_desc')

node_species
------------
::

    'node_id' varchar(64) NOT NULL:     mapped node identifier
    'taxon' int(11) NOT NULL:           taxon id of node species, 0 if property
    PRIMARY KEY ('node_id','taxon')
    KEY 'taxon' ('taxon')

node_type
---------
::

    'n_type' varchar(12) NOT NULL:  type of node ('Gene', 'Property')
    'n_type_desc' text:             description of node type
    PRIMARY KEY ('n_type')

raw_file
--------
::

    'file_id' varchar(80) NOT NULL:             processed name of downloaded
                                                file (source.alias)
    'remote_url' varchar(255) NOT NULL:         url of file on the remote source
    'remote_date' varchar(40) DEFAULT NULL:     modification date of file on the
                                                remote source
    'remote_version' varchar(40) DEFAULT NULL:  release version of the remote
                                                source
    'remote_size' bigint(11) DEFAULT NULL:      size of file on the remote source
    'source_url' varchar(255) DEFAULT NULL:     url of the homepage of the source
    'image' varchar(255) DEFAULT NULL:          url of an image for the source
    'reference' varchar(512) DEFAULT NULL:      reference for the source
    'date_downloaded' datetime NOT NULL:        date source was last downloaded
    'local_filename' varchar(255) NOT NULL:     name of the downloaded file on
                                                local disk
    'checksum' varchar(80) DEFAULT NULL:        md5 checksum of the downloaded
                                                file
    PRIMARY KEY ('file_id')

raw_line
--------
::

    'line_hash' varchar(40) NOT NULL:   md5 checksum of rawline field
    'line num' int(11) NOT NULL:        line number in downloaded file
    'file_id' varchar(80) NOT NULL:     processed name of downloaded file 
                                        (source.alias)
    'line_str' text NOT NULL:           original line string from downloaded source

species
-------
::

  'taxon' int(11) NOT NULL:                     taxon id of organism species
  'sp_abbrev' varchar(8) DEFAULT NULL:          abbreviated name of species
  'sp_sciname' varchar(255) NOT NULL:           species scientific name
  'representative' varchar(255) DEFAULT NULL:   representative species
                                                scientific name
  PRIMARY KEY ('taxon')

status
------
::

    'table_hash' varchar(40) NOT NULL:      md5 checksum of raw edge generated
                                            from source line
    'n1_id' varchar(64) NOT NULL:           node 1 mapped identifier
    'n2_id' varchar(64) NOT NULL:           node 2 mapped identifier
    'et_name' varchar(80) NOT NULL:         name edge type
    'weight' float NOT NULL:                score for edge type
    'edge_hash' varchar(40) NOT NULL:       md5 checksum of mapped edge
    'line_hash' varchar(40) NOT NULL:       md5 checksum of original line string
                                            from source
    'status' varchar(80) NOT NULL:          "production" if both nodes mapped
                                            and "unmapped" otherwise
    'status_desc' varchar(255) NOT NULL:    description of reason for status
                                            label
    PRIMARY KEY ('table_hash')
    KEY ('status_desc')
    KEY ('et_name')

