"""Extension of utilities.py to provide functions required to check the
version information of go and determine if it needs to be updated.

Classes:
    Go: extends the SrcClass class and provides the static variables and
        go specific functions required to perform a check on go.

Functions:
    main: runs compare_versions (see utilities.py) on a Go object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import re
import time

class Go(SrcClass):
    """Extends SrcClass to provide go specific check functions.

    This Go class provides source-specific functions that check the go version
    information and determine if it differs from the current version in the
    Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Stringdb with the staticly defined parameters.
        
        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'go'
        url_base = 'http://geneontology.org//gene-associations/'
        aliases = {
            "fb": "Drosophila melanogaster",
            "goa_human": "Homo sapiens",
            "mgi": "Mus musculus",
            "obo": "ontology",
            "sgd": "Saccharomyces cerevisiae",
            "tair": "Arabidopsis thaliana",
            "wb": "Caenorhabditis elegans"
        }
        super(Go, self).__init__(name, url_base, aliases)

    def get_source_version(self, alias):
        """Return the release version of the remote go:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be 'unknown' for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        return super(Go, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See utilities.SrcClass.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Go, self).get_local_file_info(alias)

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
        return super(Go, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the date modified of the remote file for the given alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        url_download_page = ('http://geneontology.org/gene-associations/'
                             'go_annotation_metadata.all.js')
        response = urllib.request.urlopen(url_download_page)
        cur_id = ''
        ret_str = ''
        t_format = "%m/%d/%Y"
        for line in response:
            d_line = line.decode()
            alias_match = re.search(r'"id": "(\S+)",', d_line)
            if alias_match is not None:
                if alias_match.group(1) == alias:
                    cur_id = alias
                else:
                    cur_id = ''
            date_match = re.search(r'"submissionDate": "(\S+)"', d_line)
            if (date_match is not None) and (cur_id == alias):
                t_str = date_match.group(1)
                ret_str = time.mktime(time.strptime(t_str, t_format))
                break
        response.close()
        return ret_str

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and alias information.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """        
        url = self.url_base + 'gene_association.' + alias + '.gz'
        # format for ontology information
        if alias == 'obo':
            url = 'http://purl.obolibrary.org/obo/go.obo'
        return url


if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Go object.

    This runs the compare_versions function on a Go object to find the version
    information of the source and determine if a fetch is needed. The version
    information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Go.
    """
    compare_versions(Go())
