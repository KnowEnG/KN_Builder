CREATE DATABASE IF NOT EXISTS KnowNet;
USE KnowNet;

CREATE TABLE IF NOT EXISTS `raw_line` (
  `line_id` int(11) NOT NULL AUTO_INCREMENT,
  `line_hash` varchar(40) NOT NULL,
  `line_str` text NOT NULL,
  PRIMARY KEY (`line_id`),
  UNIQUE KEY `line_hash` (`line_hash`)
) ENGINE=InnoDB AUTO_INCREMENT=17113779 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `raw_file` (
  `file_id` int(11) NOT NULL AUTO_INCREMENT,
  `remote_url` varchar(255) NOT NULL,
  `remote_date` varchar(40) DEFAULT NULL,
  `remote_version` varchar(40) DEFAULT NULL,
  `remote_size` int(11) DEFAULT NULL,
  `date_downloaded` datetime NOT NULL,
  `local_filename` varchar(255) NOT NULL,
  `checksum` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`file_id`),
  UNIQUE KEY `idx_raw_file_local_filename` (`local_filename`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `raw_data` (
  `data_id` int(11) NOT NULL AUTO_INCREMENT,
  `file_id` int(11) NOT NULL,
  `line_id` int(11) NOT NULL,
  `line_num` int(11) DEFAULT NULL,
  PRIMARY KEY (`data_id`),
  UNIQUE KEY `idx_raw_data_key` (`file_id`,`line_id`),
  KEY `line_id` (`line_id`),
  CONSTRAINT `raw_data_ibfk_1` FOREIGN KEY (`file_id`) REFERENCES `raw_file` (`file_id`) ON DELETE CASCADE,
  CONSTRAINT `raw_data_ibfk_2` FOREIGN KEY (`line_id`) REFERENCES `raw_line` (`line_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17113774 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `operation` (
  `file_id` int(11) NOT NULL,
  `operation` varchar(40) NOT NULL,
  `op_date` datetime NOT NULL,
  KEY `file_id` (`file_id`),
  CONSTRAINT `operation_ibfk_1` FOREIGN KEY (`file_id`) REFERENCES `raw_file` (`file_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `species` (
  `taxon` int(11) NOT NULL,
  `sp_abbrev` varchar(8) DEFAULT NULL,
  `sp_sciname` varchar(255) NOT NULL,
  `representative` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`taxon`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node_type` (
  `n_type_id` int(11) NOT NULL AUTO_INCREMENT,
  `n_type_desc` varchar(80) NOT NULL,
  PRIMARY KEY (`n_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node` (
  `node_id` int(11) NOT NULL AUTO_INCREMENT,
  `n_alias` varchar(80) NOT NULL,
  `n_orig_name` varchar(255) DEFAULT NULL,
  `n_type_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`node_id`),
  UNIQUE KEY `n_orig_name` (`n_orig_name`)
) ENGINE=InnoDB AUTO_INCREMENT=84464 DEFAULT CHARSET=latin1;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE IF NOT EXISTS `node_meta` (
  `node_id` int(11) NOT NULL,
  `info_type` varchar(80) NOT NULL,
  `info_desc` varchar(255) NOT NULL,
  UNIQUE KEY `idx_node_meta_key` (`node_id`,`info_type`,`info_desc`),
  CONSTRAINT `node_meta_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `node` (`node_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `node_species` (
  `node_id` int(11) NOT NULL,
  `taxon` int(11) NOT NULL,
  UNIQUE KEY `node_species_key` (`node_id`,`taxon`),
  KEY `taxon` (`taxon`),
  CONSTRAINT `node_species_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `node` (`node_id`) ON DELETE CASCADE,
  CONSTRAINT `node_species_ibfk_2` FOREIGN KEY (`taxon`) REFERENCES `species` (`taxon`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge_type` (
  `e_type_id` int(11) NOT NULL AUTO_INCREMENT,
  `et_name` varchar(80) NOT NULL,
  `n1_type` int(11) NOT NULL,
  `n2_type` int(11) NOT NULL,
  `bidir` tinyint(1) NOT NULL,
  `et_desc` text,
  `sc_desc` text,
  `sc_best` float DEFAULT NULL,
  `sc_worst` float DEFAULT NULL,
  PRIMARY KEY (`e_type_id`),
  UNIQUE KEY `idx_edge_type_et_name` (`et_name`),
  KEY `n1_type` (`n1_type`),
  KEY `n2_type` (`n2_type`),
  CONSTRAINT `edge_type_ibfk_1` FOREIGN KEY (`n1_type`) REFERENCES `node_type` (`n_type_id`) ON DELETE CASCADE,
  CONSTRAINT `edge_type_ibfk_2` FOREIGN KEY (`n2_type`) REFERENCES `node_type` (`n_type_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge` (
  `edge_id` int(11) NOT NULL AUTO_INCREMENT,
  `n1_id` int(11) NOT NULL,
  `n2_id` int(11) NOT NULL,
  `data_id` int(11) NOT NULL,
  `e_type_id` int(11) NOT NULL,
  `weight` float NOT NULL,
  `status` varchar(40) NOT NULL,
  `status_desc` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`edge_id`),
  UNIQUE KEY `idx_edge_key` (`n1_id`,`n2_id`,`data_id`,`e_type_id`),
  KEY `n1_id` (`n1_id`),
  KEY `n2_id` (`n2_id`),
  KEY `data_id` (`data_id`),
  KEY `e_type_id` (`e_type_id`),
  CONSTRAINT `edge_ibfk_1` FOREIGN KEY (`n1_id`) REFERENCES `node` (`node_id`) ON DELETE CASCADE,
  CONSTRAINT `edge_ibfk_2` FOREIGN KEY (`n2_id`) REFERENCES `node` (`node_id`) ON DELETE CASCADE,
  CONSTRAINT `edge_ibfk_3` FOREIGN KEY (`data_id`) REFERENCES `raw_data` (`data_id`) ON DELETE CASCADE,
  CONSTRAINT `edge_ibfk_4` FOREIGN KEY (`e_type_id`) REFERENCES `edge_type` (`e_type_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=27943626 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `edge_meta` (
  `edge_id` int(11) NOT NULL,
  `info_type` varchar(80) NOT NULL,
  `info_desc` varchar(255) NOT NULL,
  UNIQUE KEY `idx_edge_meta_key` (`edge_id`,`info_type`,`info_desc`),
  CONSTRAINT `edge_meta_ibfk_1` FOREIGN KEY (`edge_id`) REFERENCES `edge` (`edge_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `all_mappings` (
  `dbprimary_acc` varchar(512) DEFAULT NULL,
  `display_label` varchar(512) DEFAULT NULL,
  `db_name` varchar(100) NOT NULL,
  `priority` int(11) NOT NULL,
  `db_display_name` varchar(255) DEFAULT NULL,
  `stable_id` varchar(128) DEFAULT NULL,
  `species` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


