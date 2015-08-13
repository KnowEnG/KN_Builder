"""Extension of utilities.py to provide functions required to check the
version information of intact and determine if it needs to be updated.

Classes:
    Intact: Extends the SrcClass class and provides the static variables and
        intact specific functions required to perform a check on intact.

Functions:
    get_SrcClass: returns an Intact object
    main: runs compare_versions (see utilities.py) on a Intact object
"""
from utilities import SrcClass, compare_versions
import time
import ftplib

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Intact()

class Intact(SrcClass):
    """Extends SrcClass to provide intact specific check functions.

    This Intact class provides source-specific functions that check the
    intact version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Intact with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'intact'
        url_base = 'ftp.ebi.ac.uk'
        aliases = {"PPI": "PPI"}
        comment_strs = ['#']
        super(Intact, self).__init__(name, url_base, aliases)
        self.remote_file = 'intact.txt'

    def get_source_version(self, alias):
        """Return the release version of the remote intact:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias and is 'unknown' in
        this case. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        return super(Intact, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Intact, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see utilities.get_remote_file_size).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        ftp = ftplib.FTP(self.url_base)
        ftp.login()
        ftp.cwd('/pub/databases/intact/current/psimitab/')
        file_size = ftp.size('intact.zip')
        ftp.quit()
        return file_size

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
        ftp = ftplib.FTP(self.url_base)
        ftp.login()
        ftp.cwd('/pub/databases/intact/current/psimitab/')
        time_str = ftp.sendcmd('MDTM intact.zip')
        time_str = time_str[4:]
        ftp.quit()
        time_format = "%Y%m%d%H%M%S"
        return time.mktime(time.strptime(time_str, time_format))

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
        url = self.url_base + '/pub/databases/intact/current/psimitab/'
        url += 'intact.zip'
        return 'ftp://' + url

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
        return super(Intact, self).is_map(alias)

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
        
        return super(Intact, self).get_dependencies(alias)

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a intact
    object

    This runs the compare_versions function on a intact object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in intact.
    """
    compare_versions(Intact())
