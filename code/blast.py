"""Extension of utilities.py to provide functions required to check the
version information of blast and determine if it needs to be updated.

Classes:
    Blast: Extends the SrcClass class and provides the static variables and
        blast specific functions required to perform a check on blast.

Functions:
    main: runs compare_versions (see utilities.py) on a Blast object
"""
from utilities import SrcClass, compare_versions

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
