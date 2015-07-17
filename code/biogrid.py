"""Extension of utilities.py to provide functions required to check the
version information of biogrid and determine if it needs to be updated.

Classes:
    Biogrid: Extends the SrcClass class and provides the static variables and
        biogrid specific functions required to perform a check on biogrid.

Functions:
    main: runs compare_versions (see utilities.py) on a Biogrid object
"""
from utilities import SrcClass, compare_versions
import urllib.request

class Biogrid(SrcClass):
    """Extends SrcClass to provide biogrid specific check functions.

    This Biogrid class provides source-specific functions that check the
    biogrid version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Biogrid with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'biogrid'
        url_base = ('http://thebiogrid.org/downloads/archives/'
                    'Latest%20Release/BIOGRID-ALL-LATEST.mitab.zip')
        aliases = {"PPI": "PPI"}
        super(Biogrid, self).__init__(name, url_base, aliases)
        self.access_key = '2fe900033b39209b8f63d531fcb24790'

    def get_source_version(self, alias):
        """Return the release version of the remote biogrid:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Biogrid, self).get_source_version(alias)
        if version == 'unknown':
            url = 'http://webservice.thebiogrid.org/version?accesskey='
            response = urllib.request.urlopen(url + self.access_key)
            self.version[alias] = response.read().decode()
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
        return super(Biogrid, self).get_local_file_info(alias)

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
        return super(Biogrid, self).get_remote_file_size(url)

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
        return super(Biogrid, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        (See utilities.SrcClass.get_remote_url)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        return super(Biogrid, self).get_remote_url(alias)

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a biogrid
    object

    This runs the compare_versions function on a biogrid object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in biogrid.
    """
    compare_versions(Biogrid())
