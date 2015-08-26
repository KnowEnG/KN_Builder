"""Extension of utilities.py to provide functions required to check the
version information of blast and determine if it needs to be updated.

Classes:
    Blast: Extends the SrcClass class and provides the static variables and
        blast specific functions required to perform a check on blast.

Functions:
    get_SrcClass: returns a Blast object
    main: runs compare_versions (see utilities.py) on a Blast object
"""
from check_utilities import SrcClass, compare_versions
import os
import json
import csv
import math

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Blast()

class Blast(SrcClass):
    """Extends SrcClass to provide blast specific check functions.

    This Blast class provides source-specific functions that check the
    blast version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Blast with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'blast'
        url_base = 'http://veda.cs.uiuc.edu/blast/'
        aliases = {"mm9_Atha10": "10090_3702",
                   "mm9_Scer64": "10090_4932",
                   "mm9_Cele235": "10090_6239",
                   "mm9_Dmel5": "10090_7227",
                   "mm9_hg19": "10090_9606",
                   "mm9_mm9": "10090_10090",
                   "hg19_Atha10": "9606_3702",
                   "hg19_Scer64": "9606_4932",
                   "hg19_Cele235": "9606_6239",
                   "hg19_Dmel5": "9606_7227",
                   "hg19_hg19": "9606_9606",
                   "Dmel5_Atha10": "7227_3702",
                   "Dmel5_Scer64": "7227_4932",
                   "Dmel5_Cele235": "7227_6239",
                   "Dmel5_Dmel5": "7227_7227",
                   "Cele235_Atha10": "6239_3702",
                   "Cele235_Scer64": "6239_4932",
                   "Cele235_Cele235": "6239_6239",
                   "Scer64_Atha10": "4932_3702",
                   "Scer64_Scer64": "4932_4932",
                   "Atha10_Atha10": "3702_3702"}
        super(Blast, self).__init__(name, url_base, aliases)
        self.sc_max =  100  # may want to load these
        self.sc_min =  2 # may want to load these

    def get_source_version(self, alias):
        """Return the release version of the remote blast:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias and is 'unknown' in
        this case. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        return super(Blast, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.SrcClass.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Blast, self).get_local_file_info(alias)

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
        return super(Blast, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see
        utilities.SrcClass.get_remote_file_modified).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        url = self.get_remote_url(alias)
        return super(Blast, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        url = self.url_base + alias + '.out'
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
        return super(Blast, self).is_map(alias)

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
        return super(Blast, self).get_dependencies(alias)

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
        return super(Blast, self).create_mapping_dict(filename)

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
        table_file = rawline.replace('rawline','edge')
        #n_meta_file = rawline.replace('rawline','node_meta')
        #e_meta_file = rawline.replace('rawline','edge_meta')

        #static column values
        n1type = 'gene'
        n2type = 'gene'
        n1hint = 'Ensembl_GeneID'
        n2hint = 'Ensembl_GeneID'
        et_hint = 'blastp_homology'
        #node_num = 1
        #info_type = 'synonym'
        alias = version_dict['alias']

        n1spec = int(version_dict['alias_info'].split('_', 1)[0])
        n2spec = int(version_dict['alias_info'].split('_', 1)[1])

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges:
            reader = csv.reader(infile, delimiter='\t')
            edge_writer = csv.writer(edges, delimiter='\t')
            for line in reader:
                chksm = line[2]
                raw = line[3:]
                n1 = raw[0]
                n2 = raw[1]
                evalue = raw[10]
                evalue = float(evalue)
                score = self.sc_min
                if(evalue == 0.0):
                    score = self.sc_max
                if(evalue > 0.0):
                    score = round(-1.0*math.log10(evalue),4)
                if(score > self.sc_max):
                    score = self.sc_max
                if(score < self.sc_min):
                    score = self.sc_min
                
                edge_writer.writerow([chksm, n1, n1hint, n1type, n1spec, \
                    n2, n2hint, n2type, n2spec, et_hint, score])


if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a blast
    object

    This runs the compare_versions function on a blast object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in blast.
    """
    compare_versions(Blast())
