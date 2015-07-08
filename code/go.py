"""Executable containing all of the functions needed to check if go
has updated. Checks the source and outputs the updated dictionary to file."""
from utilities import SrcClass, compare_versions
import urllib.request
import re
import time

class Go(SrcClass):
    """Class providing the check functions for the source go"""
    def __init__(self):
        """Constructor for the Go class"""
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
        """Returns the source version information.
            and updates the self.version dict
            By default, returns the empty string."""
        return super(Go, self).get_source_version(alias)

    def get_local_file_info(self, alias):
        """Returns a dictionary contianing the local file information for
        source:alias which includes the local file name and a boolean that is
        True if the file exists. If the file does exist, the dictionary also
        contains the local file size and modified date"""
        return super(Go, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Returns the file size of source:alias as a string.
            Updates the url and calls the super method."""
        url = self.get_remote_url(alias)
        return super(Go, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Returns the file modified time of source:alias as seconds since
        last epoch."""
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
        """Returns the remote url to be used for source:alias in a fetch"""
        url = self.url_base + 'gene_association.' + alias + '.gz'
        # format for ontology information
        if alias == 'obo':
            url = 'http://purl.obolibrary.org/obo/go.obo'
        return url


if __name__ == "__main__":
    compare_versions(Go())
