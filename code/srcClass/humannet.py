"""Extension of utilities.py to provide functions required to check the
version information of intact and determine if it needs to be updated.

Classes:
    HumanNet: Extends the SrcClass class and provides the static variables and
        intact specific functions required to perform a check on intact.

Functions:
    get_SrcClass: returns an HumanNet object
    main: runs compare_versions (see utilities.py) on a Intact object
"""
from check_utilities import SrcClass, compare_versions
import config_utilities as cf
import csv
import hashlib

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return HumanNet(args)

class HumanNet(SrcClass):
    """Extends SrcClass to provide intact specific check functions.

    This HumanNet class provides source-specific functions that check the
    intact version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Intact with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'humannet'
        url_base = 'www.functionalnet.org'
        aliases = {"HumanNet": "HumanNet.v1.join"}
        super(HumanNet, self).__init__(name, url_base, aliases, args)
        self.remote_file = 'HumanNet.v1.join.txt'
        self.chunk_size = 250000

        self.source_url = "http://www.functionalnet.org/humannet/about.html"
        self.image = "http://www.functionalnet.org/humannet/img_files/cover_title.jpg"
        self.reference = "Lee I, Blom UM, Wang PI, Shim JE, Marcotte EM. Prioritizing candidate disease genes by network-based boosting of genome-wide association data. Genome Res. 2011;21(7):1109-21."

    def get_source_version(self, alias):
        """Return the release version of the remote HumanNet:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias and is 'unknown' in
        this case. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        return super(HumanNet, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(HumanNet, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see utilities.get_remote_file_size).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        url = self.get_remote_url(alias)
        return super(HumanNet, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see utilities.get_remote_file_modified).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        url = self.get_remote_url(alias)
        return super(HumanNet, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url, alias, and source
        version information.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        url = self.url_base + '/humannet/'
        url += 'HumanNet.v1.join.txt'
        return 'http://' + url

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
        return super(HumanNet, self).is_map(alias)

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
        return super(HumanNet, self).get_dependencies(alias)

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
        return super(HumanNet, self).create_mapping_dict(filename)

    def table(self, raw_line, version_dict):
        """Uses the provided raw_lines file to produce a 2table_edge file, an
        edge_meta file, a node and/or node_meta file (only for property nodes).

        This returns noting but produces the table formatted files from the
        provided raw_line file:
            raw_line (line_hash, line_num, file_id, raw_line)
            table_file (line_hash, n1name, n1hint, n1type, n1spec,
                     n2name, n2hint, n2type, n2spec, et_hint, score,
                     table_hash)
            edge_meta (line_hash, info_type, info_desc)
            node_meta (node_id, 
                    info_type (evidence, relationship, experiment, or link), 
                    info_desc (text))
            node (node_id, n_alias, n_type)

        Args:
            raw_line(str): The path to the raw_lines file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """
        edge_types = ["hn_CE_CC", "hn_CE_CX", "hn_CE_GT", "hn_CE_LC", "hn_CE_YH",
                      "hn_DM_PI", "hn_HS_CC", "hn_HS_CX", "hn_HS_DC", "hn_HS_GN",
                      "hn_HS_LC", "hn_HS_MS", "hn_HS_PG", "hn_HS_YH", "hn_SC_CC",
                      "hn_SC_CX", "hn_SC_GT", "hn_SC_LC", "hn_SC_MS", "hn_SC_TS",
                      "hn_SC_YH", "hn_IntNet"]

        #static column values
        n1hint = "EntrezGene"
        n1type = "gene"
        n1spec = "9606"
        n2hint = "EntrezGene"
        n2type = "gene"
        n2spec = "9606"

        #output file
        table_file = raw_line.replace('raw_line', 'table')

        with open(raw_line) as infile, \
            open(table_file, 'w') as edges:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if len(line) == 1:
                    continue
                chksm = line[0]
                n1name = line[3]
                n2name = line[4]
                for edge_num in range(len(line[5:])):
                    score = line[edge_num+5]
                    et_hint = edge_types[edge_num]
                    if score == 'NA':
                        continue
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1name, n1hint, n1type,
                                             n1spec, n2name, n2hint, n2type,
                                             n2spec, et_hint, str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1name, n1hint, n1type, n1spec,
                                          n2name, n2hint, n2type, n2spec,
                                          et_hint, score, t_chksum])



if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a HumanNet
    object

    This runs the compare_versions function on a intact object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in intact.
    """
    print(compare_versions(HumanNet()))
    
