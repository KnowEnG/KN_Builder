"""Extension of utilities.py to provide functions required to check the
version information of msigdb and determine if it needs to be updated.

Classes:
    Msigdb: Extends the SrcClass class and provides the static variables and
        msigdb specific functions required to perform a check on msigdb.

Functions:
    main: runs compare_versions (see utilities.py) on a Msigdb object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import re
import time

class Msigdb(SrcClass):
    """Extends SrcClass to provide msigdb specific check functions.

    This Msigdb class provides source-specific functions that check the
    msigdb version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Msigdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'msigdb'
        url_base = 'http://www.broadinstitute.org/gsea/'
        aliases = {"c2.cgp": "curated_genes_cpg",
                   "c3.mir": "motif_gene_mir",
                   "c4.cgn": "comp_genes_cgn",
                   "c4.cm": "onco_sigs_cm",
                   "c6.all": "oncogenic_signatures_all",
                   "c7.all": "immunologic_signatures_all"}
        super(Msigdb, self).__init__(name, url_base, aliases)
        self.date_modified = 'unknown'

    def get_source_version(self, alias):
        """Return the release version of the remote msigdb:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Msigdb, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'msigdb/help.jsp'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                try:
                    d_line = line.decode()
                except:
                    continue
                match = re.search('MSigDB database v([^ ]*)', d_line)
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
        return super(Msigdb, self).get_local_file_info(alias)

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
        return super(Msigdb, self).get_remote_file_size(url)

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
            url = self.url_base + 'msigdb/help.jsp'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode('ascii', errors='ignore')
                match = re.search('updated ([^<]*)', d_line)
                if match is not None:
                    time_str = match.group(1)
                    response.close()
                    break
            time_format = "%B %Y"
            date_modified = time.mktime(time.strptime(time_str, time_format))
            self.date_modified = date_modified
        return self.date_modified

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
        url = self.url_base + 'resources/msigdb/' + version + '/'
        url += alias + '.v' + version + '.entrez.gmt'
        return url

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Msigdb
    object

    This runs the compare_versions function on a Msigdb object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Msigdb.
    """
    compare_versions(Msigdb())
