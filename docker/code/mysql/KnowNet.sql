CREATE DATABASE IF NOT EXISTS KnowNet;
USE KnowNet;

CREATE TABLE IF NOT EXISTS `all_mappings` (
  `dbprimary_acc` varchar(512) DEFAULT NULL,
  `display_label` varchar(512) DEFAULT NULL,
  `db_name` varchar(100) NOT NULL,
  `priority` int(11) NOT NULL,
  `db_display_name` varchar(255) DEFAULT NULL,
  `stable_id` varchar(128) DEFAULT NULL,
  `species` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge` (
  `n1_id` varchar(64) NOT NULL,
  `n2_id` varchar(64) NOT NULL,
  `et_name` varchar(80) NOT NULL,
  `weight` float NOT NULL,
  `edge_hash` varchar(40) NOT NULL,
  PRIMARY KEY (`n1_id`, `n2_id`, `et_name`),
  KEY `n2_id` (`n2_id`),
  KEY `et_name` (`et_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge2line`(
  `edge_hash` varchar(40) NOT NULL,
  `line_hash` varchar(40) NOT NULL,
  PRIMARY KEY (`edge_hash`, `line_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge_meta` (
  `line_hash` varchar(40) NOT NULL,
  `info_type` varchar(80) NOT NULL,
  `info_desc` varchar(255) NOT NULL,
  PRIMARY KEY (`line_hash`,`info_type`,`info_desc`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge_type` (
  `et_name` varchar(80) NOT NULL,
  `n1_type` varchar(12) NOT NULL,
  `n2_type` varchar(12) NOT NULL,
  `bidir` tinyint(1) NOT NULL,
  `et_desc` text,
  `sc_desc` text,
  `sc_best` float DEFAULT NULL,
  `sc_worst` float DEFAULT NULL,
  PRIMARY KEY (`et_name`),
  KEY (`n1_type`),
  KEY (`n2_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node` (
  `node_id` varchar(64) NOT NULL,
  `n_alias` varchar(512) DEFAULT NULL,
  `n_type` varchar(12) DEFAULT NULL,
  PRIMARY KEY (`node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node_meta` (
  `node_id` varchar(64) NOT NULL,
  `info_type` varchar(80) NOT NULL,
  `info_desc` varchar(255) NOT NULL,
  PRIMARY KEY (`node_id`,`info_type`,`info_desc`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node_species` (
  `node_id` varchar(64) NOT NULL,
  `taxon` int(11) NOT NULL,
  PRIMARY KEY (`node_id`,`taxon`),
  KEY `taxon` (`taxon`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node_type` (
  `n_type` varchar(12) NOT NULL,
  `n_type_desc` text,
  PRIMARY KEY (`n_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `raw_file` (
  `file_id` varchar(80) NOT NULL,
  `remote_url` varchar(255) NOT NULL,
  `remote_date` varchar(40) DEFAULT NULL,
  `remote_version` varchar(40) DEFAULT NULL,
  `remote_size` bigint(11) DEFAULT NULL,
  `source_url` varchar(255) DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL,
  `reference` varchar(512) DEFAULT NULL,
  `pmid` int(11) DEFAULT NULL,
  `license` varchar(512) DEFAULT NULL,
  `date_downloaded` varchar(40) DEFAULT NULL,
  `local_filename` varchar(255) NOT NULL,
  `checksum` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `log` (
  `filename` varchar(255) NOT NULL,
  `info_type` varchar(255) NOT NULL,
  `info_value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`filename`, `info_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `raw_line` (
  `line_hash` varchar(40) NOT NULL,
  `line_num` int(11) NOT NULL,
  `file_id` varchar(80) NOT NULL,
  `line_str` text NOT NULL,
  PRIMARY KEY (`line_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `species` (
  `taxon` int(11) NOT NULL,
  `sp_abbrev` varchar(8) DEFAULT NULL,
  `sp_sciname` varchar(255) NOT NULL,
  `representative` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`taxon`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `status` (
  `table_hash` varchar(40) NOT NULL,
  `n1_id` varchar(64) NOT NULL,
  `n2_id` varchar(64) NOT NULL,
  `et_name` varchar(80) NOT NULL,
  `weight` float NOT NULL,
  `edge_hash` varchar(40) NOT NULL,
  `line_hash` varchar(40) NOT NULL,
  `status` varchar(80) NOT NULL,
  `status_desc` varchar(255) NOT NULL,
  PRIMARY KEY (`table_hash`),
  KEY (`status_desc`),
  KEY (`et_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

