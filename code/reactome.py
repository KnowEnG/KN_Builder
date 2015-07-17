"""Extension of utilities.py to provide functions required to check the
version information of reactome and determine if it needs to be updated.

Classes:
    Reactome: Extends the SrcClass class and provides the static variables and
        reactome specific functions required to perform a check on reactome.

Functions:
    main: runs compare_versions (see utilities.py) on a Reactome object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import re

class Reactome(SrcClass):
    """Extends SrcClass to provide reactome specific check functions.

    This Reactome class provides source-specific functions that check the
    reactome version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Reactome with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'reactome'
        url_base = 'http://www.reactome.org/'
        aliases = {"Ensembl2Reactome_All_Levels": "genes2pathways",
                   "ReactomePathways": "reactomePathways",
                   "homo_sapiens.interactions": "pathwayInteractions",
                   "ReactomePathwaysRelation":"ReactomeRelations"}
        super(Reactome, self).__init__(name, url_base, aliases)

    def get_source_version(self, alias):
        """Return the release version of the remote reactome:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Reactome, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'category/reactome-announcement/'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search('Version (\d+)', d_line)
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
        return super(Reactome, self).get_local_file_info(alias)

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
        return super(Reactome, self).get_remote_file_size(url)

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
        return super(Reactome, self).get_remote_file_modified(url)

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
        url = self.url_base + 'download/current/'
        if 'interactions' in alias:
            url += alias + '.txt.gz'
        else:
            url += alias + '.txt'
        return url

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Reactome
    object

    This runs the compare_versions function on a Reactome object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Reactome.
    """
    compare_versions(Reactome())
