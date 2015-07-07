from source_utils import *
from urllib2 import urlopen
import re

class Stringdb(SrcClass):
    def __init__(self):
        name = 'stringdb'
        url_base = 'http://string-db.org/'
        aliases =   {"10090": "Mmus",
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
            response = urlopen(self.url_base)
            the_page = response.readlines()
            for line in the_page:
                match = re.search('This is version ([^ ]*) of STRING', line)
                if match is not None:
                    response.close()
                    self.version[alias] = match.group(1)
        return self.version[alias]

    def get_source_version_date(self):
        pass
    
    def get_local_file_info(self, alias):
        """Returns the local file version information as defined in SrcClass"""
        return super(Stringdb, self).get_local_file_info(alias)
    
    def get_remote_file_size(self, alias):
        """Returns the file size of source:alias as a string.
            Updates the url and calls the super method."""
        url = self.get_remote_url(alias)
        return super(Stringdb, self).get_remote_file_size(url)

    def get_remote_file_modified(self, alias):
        """Returns the file modified time of source:alias as a string.
            Updates the url and calls the super method."""
        url = self.get_remote_url(alias)
        return super(Stringdb, self).get_remote_file_modified(url)
        
    def get_remote_url(self, alias):
        """Returns the remote url to be used for source:alias in a fetch"""
        version = self.get_source_version(alias)
        url = self.url_base + 'newstring_download/protein.links.detailed.v'
        url += version + '/' + alias + '.protein.links.detailed.v'
        url += version + '.txt.gz'
        return url


if __name__ == "__main__":
    process_src(Stringdb())