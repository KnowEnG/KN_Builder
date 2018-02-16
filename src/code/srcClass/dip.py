"""Extension of utilities.py to provide functions required to check the
version information of dip and determine if it needs to be updated.

Classes:
    Dip: Extends the SrcClass class and provides the static variables and
        dip specific functions required to perform a check on dip.

Functions:
    main: runs compare_versions (see utilities.py) on a Dip object
"""
import urllib.request
import re
import os
import json
import config_utilities as cf
from check_utilities import SrcClass, compare_versions
from mitab_utilities import table

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Dip(args)

class Dip(SrcClass):
    """Extends SrcClass to provide dip specific check functions.

    This Dip class provides source-specific functions that check the
    dip version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Dip with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'dip'
        url_base = 'http://dip.doe-mbi.ucla.edu/dip/script/files/'
        aliases = {"PPI": "PPI"}
        super(Dip, self).__init__(name, url_base, aliases, args)
        self.year = ''
        src_data_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
        sp_dir = os.path.join(src_data_dir, 'species', 'species.json')
        sp_dict = json.load(open(sp_dir))
        self.taxid_list = sp_dict.values()

        self.source_url = "http://dip.doe-mbi.ucla.edu/"
        self.image = "https://www.virtuallyimmune.org/wp-content/uploads/2014/07/dip_logo.png"
        self.reference = ("Salwinski L, Miller CS, Smith AJ, Pettit FK, Bowie JU, Eisenberg D. The "
                          "Database of Interacting Proteins: 2004 update. Nucleic Acids Res. "
                          "2004;32(Database issue):D449-51.")
        self.pmid = 14681454
        self.license = ('<a href="http://creativecommons.org/licenses/by-nd/3.0/">Creative Commons '
                        'Attribution-NoDerivs License</a>. However, if you intend to distribute '
                        'data from our database, you must <a href="mailto:dip@mbi.ucla.edu">ask '
                        'us</a> for permission first.')

    def get_source_version(self, alias):
        """Return the release version of the remote dip:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Dip, self).get_source_version(alias)
        if version == 'unknown':
            #get the year to provide a more accurate base_url
            if self.year == '':
                response = urllib.request.urlopen(self.url_base)
                for line in response:
                    d_line = line.decode()
                    year_match = re.search(r'href="(\d{4}/)"', d_line)
                    if year_match is not None:
                        if year_match.group(1) > self.year:
                            self.year = year_match.group(1)
                response.close()
            url = self.url_base + self.year + 'tab25/'
            response = urllib.request.urlopen(url)
            self.version[alias] = ''
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'href="(dip\d{8}).txt"', d_line)
                if match is not None:
                    if match.group(1) > self.version[alias]:
                        self.version[alias] = match.group(1)
            response.close()
            for alias_name in self.aliases:
                self.version[alias_name] = self.version[alias]
            return self.version[alias]
        else:
            return version

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url, source version
        information, and year source was last updated.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        version = self.get_source_version(alias)
        url = self.url_base + self.year + 'tab25/' + version + '.txt'
        return url

    def table(self, raw_line, version_dict):
        """Uses the provided raw_lines file to produce a 2table_edge file, an
        edge_meta file, a node and/or node_meta file (only for property nodes).

        This returns noting but produces the table formatted files from the
        provided raw_line file:
            raw_line (line_hash, line_num, file_id, raw_line)
            table_file (line_hash, n1name, n1hint, n1type, n1spec,
                     n2name, n2hint, n2type, n2spec, et_hint, score,
                     table_hash)
            edge_meta (line_hash, info_type, info_desc)
            node_meta (node_id,
                    info_type (evidence, relationship, experiment, or link),
                    info_desc (text))
            node (node_id, n_alias, n_type)

        Args:
            raw_line(str): The path to the raw_lines file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """
        return table(raw_line, version_dict, self.taxid_list)

def main():
    """Runs compare_versions (see utilities.compare_versions) on a dip
    object

    This runs the compare_versions function on a dip object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in dip.
    """
    compare_versions(Dip())

if __name__ == "__main__":
    main()
