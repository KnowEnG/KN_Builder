"""Extension of utilities.py to provide functions required to check the
version information of stringdb and determine if it needs to be updated.

Classes:
    Stringdb: Extends the SrcClass class and provides the static variables and
        stringdb specific functions required to perform a check on stringdb.

Functions:
    get_SrcClass: returns a Stringdb object
    main: runs compare_versions (see utilities.py) on a Stringdb object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import re

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
