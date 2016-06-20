"""Extension of utilities.py to provide functions required to check the
version information of pathcom and determine if it needs to be updated.

Classes:
    Pathcom: Extends the SrcClass class and provides the static variables and
        pathcom specific functions required to perform a check on pathcom.

Functions:
    get_SrcClass: returns a Pathcom object
    main: runs compare_versions (see utilities.py) on a Pathcom object
"""
from check_utilities import SrcClass, compare_versions
import config_utilities as cf
import urllib.request
import re
import hashlib
import csv
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
    return Pathcom(args)

class Pathcom(SrcClass):
    """Extends SrcClass to provide pathcom specific check functions.

    This Pathcom class provides source-specific functions that check the
    pathcom version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Pathcom with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'pathcom'
        url_base = 'http://www.pathwaycommons.org/archives/PC2/current/'
        aliases = {"all":""}
        super(Pathcom, self).__init__(name, url_base, aliases, args)

    def get_source_version(self, alias):
        """Return the release version of the remote pathcom:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Pathcom, self).get_source_version(alias)
        if version == 'unknown':
            response = urllib.request.urlopen(self.url_base + 'datasources.txt')
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search('Pathway Commons version ([^ ]*)', d_line)
                if match is not None:
                    response.close()
                    self.version[alias] = match.group(1)
                    break
            for alias_name in self.aliases:
                self.version[alias_name] = match.group(1)
            return self.version[alias]
        else:
            return version

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.SrcClass.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Pathcom, self).get_local_file_info(alias)

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
        return super(Pathcom, self).get_remote_file_size(url)

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
        return super(Pathcom, self).get_remote_file_modified(url)

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
        url = self.url_base
        url += 'PathwayCommons.8.All.EXTENDED_BINARY_SIF.hgnc.txt.gz'
        url = url.format(self.get_source_version(alias))
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
        return super(Pathcom, self).is_map(alias)

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
        return super(Pathcom, self).get_dependencies(alias)

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
        return super(Pathcom, self).create_mapping_dict(filename)

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
        e_meta_file = rawline.replace('rawline', 'edge_meta')

        #static column values
        n1type = 'gene' #ignoring chemicals
        n1hint = 'UNIPROT_GN'
        n1spec = 'unknown'
        n2type = n1type #ignoring chemicals
        n2hint = n1hint
        n2spec = n1spec
        n3_type = 'property'
        n3hint = 'unknown'
        n3spec = 'unknown'
        score = '1'
        info_type = 'alt_alias'
        n_type_id = '2'

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(e_meta_file, 'w') as e_meta, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            e_meta_writer = csv.writer(e_meta, delimiter='\t', lineterminator='\n')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if 'PARTICIPANT' in line[0]: #skip header
                    continue
                chksm = line[2]
                raw = line[3:]
                if len(raw) !=7: #extended information
                    continue
                (n1id, et_hint, n2id, src, publist, n3id, mediator_ids) = raw
                et_hint = 'pathcom_' + et_hint.replace('-', '_')
                #n1-n2 edge
                hasher = hashlib.md5()
                hasher.update('\t'.join([chksm, n1id, n1hint, n1type, n1spec,
                                         n2id, n2hint, n2type, n2spec, et_hint,
                                         score]).encode())
                t_chksum = hasher.hexdigest()
                edge_writer.writerow([chksm, n1id, n1hint, n1type, n1spec,
                                      n2id, n2hint, n2type, n2spec, et_hint,
                                      score, t_chksum])
                e_meta_writer.writerow([chksm, 'original_source', src])
                if publist:
                    e_meta_writer.writerow([chksm, 'reference', publist])
                #pathway edge
                if n3id:
                    kn_n3id = cf.pretty_name('paco_' + n3id)
                    n_writer.writerow([kn_n3id, kn_n3id, n_type_id])
                    n_meta_writer.writerow([kn_n3id, info_type, n3id])
                    for node in [n1id, n2id]:
                        hasher = hashlib.md5()
                        hasher.update('\t'.join([chksm, kn_n3id, n3hint, n3_type,
                                    n3spec,node, n1hint, n1type, n1spec,
                                    'pathcom_pathway', score]).encode())
                        t_chksum = hasher.hexdigest()
                        edge_writer.writerow([chksm, kn_n3id, n3hint, n3_type,
                                    n3spec, node, n1hint, n1type, n1spec,
                                    'pathcom_pathway', score, t_chksum])
        outfile = e_meta_file.replace('edge_meta', 'unique.edge_meta')
        tu.csu(e_meta_file, outfile, [1, 2, 3])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)


if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Pathcom
    object

    This runs the compare_versions function on a Pathcom object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Pathcom.
    """
    compare_versions(Pathcom())
