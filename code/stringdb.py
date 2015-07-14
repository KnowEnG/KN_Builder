"""Extension of utilities.py to provide functions required to check the
version information of stringdb and determine if it needs to be updated.

Classes:
    Stringdb: Extends the SrcClass class and provides the static variables and
        stringdb specific functions required to perform a check on stringdb.

Functions:
    main: runs compare_versions (see utilities.py) on a Stringdb object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import re
import time

class Stringdb(SrcClass):
    """Extends SrcClass to provide stringdb specific check functions.
    
    This Stringdb provides source-specific functions that check the strindb
    version information and determine if it differs from the current version in
    the Knowledge Network (KN).
    
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
                    for alias_name in self.aliases:
                        self.version[alias_name] = match.group(1)
            return self.version[alias]
        else:
            return version

    def get_local_file_info(self, alias):
         """Return a dictionary with the local file information for the alias.
         
         (See utilities.get_local_file_info)
         
        Args:
            alias (str): An alias defined in self.aliases.
        
        Returns:
            dict: The local file information for a given source alias.
        """            
        return super(Stringdb, self).get_local_file_info(alias)

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
        return super(Stringdb, self).get_remote_file_size(url)

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
        return super(Stringdb, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.
        
        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and source version
        information
        
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
