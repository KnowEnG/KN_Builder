"""Extension of utilities.py to provide functions required to check the
version information of pfam and determine if it needs to be updated.

Classes:
    Pfam: extends the SrcClass class and provides the static variables and
        pfam specific functions required to perform a check on go.

Functions:
    get_SrcClass: returns a Pfam object
    main: runs compare_versions (see utilities.py) on a Pfam object
"""
from check_utilities import SrcClass, compare_versions
import re
import os
import json
import csv
import hashlib
import math
import config_utilities as cf
import table_utilities as tu

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Pfam(args)

class Pfam(SrcClass):
    """Extends SrcClass to provide go specific check functions.

    This Go class provides source-specific functions that check the go version
    information and determine if it differs from the current version in the
    Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Stringdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'pfam'
        url_base = 'http://veda.cs.uiuc.edu/Pfam_domains/'
        aliases = {
            "Dmel5": "Drosophila melanogaster",
            "hg19": "Homo sapiens",
            "mm9": "Mus musculus",
            "Scer64": "Saccharomyces cerevisiae",
            "Atha10": "Arabidopsis thaliana",
            "Cele235": "Caenorhabditis elegans"
        }
        super(Pfam, self).__init__(name, url_base, aliases, args)
        self.sc_max = 100  # may want to load these
        self.sc_min = 2 # may want to load these

    def get_source_version(self, alias):
        """Return the release version of the remote pfam:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be 'unknown' for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        return super(Pfam, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.SrcClass.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Pfam, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see
        utilities.SrcClass.get_remote_file_size).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        url = self.get_remote_url(alias)
        return super(Pfam, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the date modified of the remote file for the given alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        url = self.get_remote_url(alias)
        return super(Pfam, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and alias information.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        url = self.url_base + alias + '.tblout'
        return url

    def is_map(self, alias):
        """Return a boolean representing if the provided alias is used for
        source specific mapping of nodes or edges.

        This returns a boolean representing if the alias corresponds to a file
        used for mapping. By default this returns True if the alias ends in
        '_map' and False otherwise.

        Args:
            alias(str): An alias defined in self.aliases.

        Returns:
            bool: Whether or not the alias is used for mapping.
        """
        return super(Pfam, self).is_map(alias)

    def get_dependencies(self, alias):
        """Return a list of other aliases that the provided alias depends on.

        This returns a list of other aliases that must be processed before
        full processing of the provided alias can be completed.

        Args:
            alias(str): An alias defined in self.aliases.

        Returns:
            list: The other aliases defined in self.aliases that the provided
                alias depends on.
        """
        return super(Pfam, self).get_dependencies(alias)

    def create_mapping_dict(self, filename):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in mapping nodes or edge types from
        the file specified by filetype. By default it opens the file specified
        by filename creates a dictionary using the first column as the key and
        the second column as the value.

        Args:
            filename(str): The name of the file containing the information
                needed to produce the maping dictionary.

        Returns:
            dict: A dictionary for use in mapping nodes or edge types.
        """
        return super(Pfam, self).create_mapping_dict(filename)

    def table(self, rawline, version_dict):
        """Uses the provided rawline file to produce a 2table_edge file, an
        edge_meta file, and a node_meta file (only for property nodes).

        This returns noting but produces the 2table formatted files from the
        provided rawline file:
            rawline table (file, line num, line_chksum, rawline)
            2tbl_edge table (line_cksum, n1name, n1hint, n1type, n1spec,
                            n2name, n2hint, n2type, n2spec, et_hint, score)
            edge_meta (line_cksum, info_type, info_desc)
            node_meta (line_cksum, node_num (1 or 2),
                       info_type (evidence, relationship, experiment, or link),
                       info_desc (text))

        Args:
            rawline(str): The path to the rawline file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """

        #outfiles
        table_file = rawline.replace('rawline', 'table')
        n_meta_file = rawline.replace('rawline', 'node_meta')
        node_file = rawline.replace('rawline', 'node')
        #e_meta_file = rawline.replace('rawline', 'edge_meta')

        #static column values
        n1type = 'property'
        n1_type_id = '2'
        n2type = 'gene'
        n1hint = 'Pfam/Family'
        n2hint = 'UniProt/Ensembl_GeneID'
        et_hint = 'pfam_domains'
        n1spec = '0'
        map_dict = dict()
        info_type = "alt_alias"
        src = self.name

        ###Map the file name
        species = (os.path.join('..', '..', 'id_map', 'species', 'species.json'))
        with open(species) as infile:
            species_map = json.load(infile)
        n2spec = species_map.get(version_dict['alias_info'], \
                    "unmapped:unsupported-species")

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split()
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]

                # skip commented lines
                comment_match = re.match('#', raw[0])
                if comment_match is not None:
                    continue

                orig_id = raw[1].strip()
                orig_name = raw[0].strip()
                kn_id = cf.pretty_name(src + '_' + orig_id)
                kn_name = cf.pretty_name(src + '_' + orig_name)
                map_dict[orig_id] = kn_id + '::' + kn_name
                n_writer.writerow([kn_id, kn_name, n1_type_id])
                n_meta_writer.writerow([kn_id, info_type, orig_name])
                n_meta_writer.writerow([kn_id, info_type, orig_id])
                n2orig = raw[2]
                evalue = raw[4]
                evalue = float(evalue)
                score = self.sc_min
                if evalue == 0.0:
                    score = self.sc_max
                if evalue > 0.0:
                    score = round(-1.0*math.log10(evalue), 4)
                if score > self.sc_max:
                    score = self.sc_max
                if score < self.sc_min:
                    score = self.sc_min

                hasher = hashlib.md5()
                hasher.update('\t'.join([chksm, kn_id, n1hint, n1type, n1spec, 
                                         n2orig, n2hint, n2type, n2spec, et_hint, 
                                         str(score)]).encode())
                t_chksum = hasher.hexdigest()
                edge_writer.writerow([chksm, kn_id, n1hint, n1type, n1spec, 
                                      n2orig, n2hint, n2type, n2spec, et_hint, 
                                      score, t_chksum])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)

                                      


if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Pfam object.

    This runs the compare_versions function on a Pfam object to find the version
    information of the source and determine if a fetch is needed. The version
    information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Pfam.
    """
    compare_versions(Pfam())
