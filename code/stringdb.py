"""Extension of utilities.py to provide functions required to check the
version information of stringdb and determine if it needs to be updated.

Classes:
    Stringdb: Extends the SrcClass class and provides the static variables and
        stringdb specific functions required to perform a check on stringdb.

Functions:
    get_SrcClass: returns a Stringdb object
    main: runs compare_versions (see utilities.py) on a Stringdb object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import csv

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Stringdb()

class Stringdb(SrcClass):
    """Extends SrcClass to provide stringdb specific check functions.

    This Stringdb class provides source-specific functions that check the
    stringdb version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Stringdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'stringdb'
        url_base = 'http://string-db.org/'
        aliases = {"10090": "Mmus",
                   "3702": "Atha",
                   "4932": "Scer",
                   "6239": "Cele",
                   "7227": "Dmel",
                   "9606": "Hsap"}
        super(Stringdb, self).__init__(name, url_base, aliases)

    def get_source_version(self, alias):
        """Return the release version of the remote stringdb:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Stringdb, self).get_source_version(alias)
        if version == 'unknown':
            response = urllib.request.urlopen(self.url_base)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search('This is version ([^ ]*) of STRING', d_line)
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
        return super(Stringdb, self).get_local_file_info(alias)

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
        return super(Stringdb, self).get_remote_file_size(url)

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
        return super(Stringdb, self).get_remote_file_modified(url)

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
        version = self.get_source_version(alias)
        url = self.url_base + 'newstring_download/protein.links.detailed.v'
        url += version + '/' + alias + '.protein.links.detailed.v'
        url += version + '.txt.gz'
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
        return super(Stringdb, self).is_map(alias)

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
        return super(Stringdb, self).get_dependencies(alias)

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
        return super(Stringdb, self).create_mapping_dict(filename)

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
        table_file = '.'.join(rawline.split('.')[:-2]) + '.edge.txt'
        e_meta_file = '.'.join(rawline.split('.')[:-2]) + '.edge_meta.txt'

        #static column values
        n1type = 'gene'
        n1hint = 'unknown'
        n2type = 'gene'
        n2hint = 'unknown'
        info_type = 'combined_score'
        edge_types = {2: 'STRING_neighborhood',
                      3: 'STRING_fusion',
                      4: 'STRING_cooccurence',
                      5: 'STRING_coexpression',
                      6: 'STRING_experimental',
                      7: 'STRING_database',
                      8: 'STRING_textmining'}

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(e_meta_file, 'w') as e_meta:
            reader = csv.reader(infile, delimiter='\t')
            next(reader)
            edge_writer = csv.writer(edges, delimiter='\t')
            e_meta_writer = csv.writer(e_meta, delimiter='\t')
            for line in reader:
                chksm = line[2]
                raw = line[3].split(' ')
                n1list = raw[0].split('.')
                n2list = raw[1].split('.')
                if len(n1list) < 2 or len(n2list) < 2:
                    continue
                n1spec = n1list[0]
                n1 = '.'.join(n1list[1:])
                n2spec = n2list[0]
                n2 = '.'.join(n2list[1:])
                for et in edge_types:
                    et_hint = edge_types[et]
                    score = raw[et]
                    edge_writer.writerow([chksm, n1, n1hint, n1type, n1spec, \
                            n2, n2hint, n2type, n2spec, et_hint, score])
                publist = raw[9]
                e_meta_writer.writerow([chksm, info_type, publist])

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Stringdb
    object

    This runs the compare_versions function on a Stringdb object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Stringdb.
    """
    compare_versions(Stringdb())
