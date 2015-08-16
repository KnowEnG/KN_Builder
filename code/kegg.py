"""Extension of utilities.py to provide functions required to check the
version information of kegg and determine if it needs to be updated.

Classes:
    Kegg: Extends the SrcClass class and provides the static variables and
        kegg specific functions required to perform a check on kegg.

Functions:
    get_SrcClass: returns a Kegg object
    main: runs compare_versions (see utilities.py) on a Kegg object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import time

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Kegg()

class Kegg(SrcClass):
    """Extends SrcClass to provide kegg specific check functions.

    This Kegg class provides source-specific functions that check the
    kegg version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Kegg with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'kegg'
        url_base = 'http://rest.kegg.jp/'
        aliases = {"pathway": "pathways",
                   "ath": "Arabidopsis thaliana",
                   "ath_map": "Atha_IDmap",
                   "cel": "Caenorhabditis elegans",
                   "cel_map": "Cele_IDmap",
                   "dme": "Drosophila melanogaster",
                   "dme_map": "Dmel_IDmap",
                   "hsa": "Homo sapiens",
                   "hsa_map": "Hsap_IDmap",
                   "mmu": "Mus musculus",
                   "mmu_map": "Mmus_IDmap",
                   "sce": "Saccharomyces cerevisiae",
                   "sce_map": "Scer_IDmap"}
        super(Kegg, self).__init__(name, url_base, aliases)
        self.date_modified = 'unknown'

    def get_source_version(self, alias):
        """Return the release version of the remote kegg:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias and is 'unknown' in
        this case. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Kegg, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'info/pathway'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'Release (\S+), ([^<\n]*)', d_line)
                if match is not None:
                    self.version[alias] = match.group(1)
                    response.close()
                    break
            for alias_name in self.aliases:
                self.version[alias_name] = self.version[alias]
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
        return super(Kegg, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This returns -1.0 because the remote file size is not returned by the
        REST server.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        return -1

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the remote file date modifed as specificied by the version
        information page.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        if self.date_modified == 'unknown':
            url = self.url_base + 'info/pathway'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'Release (\S+), ([^<\n]*)', d_line)
                if match is not None:
                    time_str = match.group(2)
                    response.close()
                    break
            time_format = "%b %y"
            date_modified = time.mktime(time.strptime(time_str, time_format))
            self.date_modified = date_modified
        return self.date_modified

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the alias and url_base.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        if 'map' in alias:
            url = self.url_base + 'conv/ncbi-geneid/' + alias[:-4]
        elif alias == 'pathway':
            url = self.url_base + 'list/pathway'
        else:
            url = self.url_base + 'link/' + alias + '/pathway'
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
        if alias == 'pathway':
            return True
        else:
            return super(Kegg, self).is_map(alias)

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
        if alias[-4:] == '_map' or alias == 'pathway':
            return list()
        else:
            return [alias + '_map', 'pathway']

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
        return super(Kegg, self).create_mapping_dict(filename)

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a kegg
    object

    This runs the compare_versions function on a kegg object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in kegg.
    """
    compare_versions(Kegg())
