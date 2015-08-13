"""Extension of utilities.py to provide functions required to check the
version information of dip and determine if it needs to be updated.

Classes:
    Dip: Extends the SrcClass class and provides the static variables and
        dip specific functions required to perform a check on dip.

Functions:
    main: runs compare_versions (see utilities.py) on a Dip object
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
    return Dip()

class Dip(SrcClass):
    """Extends SrcClass to provide dip specific check functions.

    This Dip class provides source-specific functions that check the
    dip version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Dip with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'dip'
        url_base = 'http://dip.doe-mbi.ucla.edu/dip/script/files/'
        aliases = {"PPI": "PPI"}
        super(Dip, self).__init__(name, url_base, aliases)
        self.year = ''

    def get_source_version(self, alias):
        """Return the release version of the remote dip:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Dip, self).get_source_version(alias)
        if version == 'unknown':
            #get the year to provide a more accurate base_url
            if self.year == '':
                response = urllib.request.urlopen(self.url_base)
                for line in response:
                    d_line = line.decode()
                    year_match = re.search(r'href="(\d{4}/)"', d_line)
                    if year_match is not None:
                        if year_match.group(1) > self.year:
                            self.year = year_match.group(1)
                response.close()
            url = self.url_base + self.year + 'tab25/'
            response = urllib.request.urlopen(url)
            self.version[alias] = ''
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'href="(dip\d{8}).txt"', d_line)
                if match is not None:
                    if match.group(1) > self.version[alias]:
                        self.version[alias] = match.group(1)
            response.close()
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
        return super(Dip, self).get_local_file_info(alias)

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
        return super(Dip, self).get_remote_file_size(url)

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
        return super(Dip, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url, source version
        information, and year source was last updated.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        version = self.get_source_version(alias)
        url = self.url_base + self.year + 'tab25/' + version + '.txt'
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
        return super(Dip, self).is_map(alias)

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
        
        return super(Dip, self).get_dependencies(alias)

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a dip
    object

    This runs the compare_versions function on a dip object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in dip.
    """
    compare_versions(Dip())
