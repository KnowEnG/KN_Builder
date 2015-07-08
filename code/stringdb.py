"""Executable containing all of the functions needed to check if stringdb
has updated. Checks the source and outputs the updated dictionary to file."""
from utilities import SrcClass, compare_versions
import urllib.request
import re
import time

class Stringdb(SrcClass):
    """Class providing the check functions for the source strindb"""
    def __init__(self):
        """Constructor for the Stringdb class"""
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
        """Returns the current version of source as a string.
            Overwrites super metod to scrape with a source specific regex.
            Alias is ignored in this context."""
        if alias not in self.version:
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

    def get_local_file_info(self, alias):
        """Returns the local file version information as defined in SrcClass"""
        return super(Stringdb, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Returns the file size of source:alias as a string.
            Updates the url and calls the super method."""
        url = self.get_remote_url(alias)
        return super(Stringdb, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Returns the file modified time of source:alias as seconds since
        last epoch. Updates the url and calls the super method."""
        url = self.get_remote_url(alias)
        t_str = super(Stringdb, self).get_remote_file_modified(url)
        t_format = "%a, %d %b %Y %H:%M:%S %Z"
        return time.mktime(time.strptime(t_str, t_format))

    def get_remote_url(self, alias):
        """Returns the remote url to be used for source:alias in a fetch"""
        version = self.get_source_version(alias)
        url = self.url_base + 'newstring_download/protein.links.detailed.v'
        url += version + '/' + alias + '.protein.links.detailed.v'
        url += version + '.txt.gz'
        return url


if __name__ == "__main__":
    compare_versions(Stringdb())
