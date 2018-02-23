"""Extension of utilities.py to provide functions required to check the
version information of biogrid and determine if it needs to be updated.

Classes:
    Biogrid: Extends the SrcClass class and provides the static variables and
        biogrid specific functions required to perform a check on biogrid.

Functions:
    get_SrcClass: returns a Biogrid object
    main: runs compare_versions (see utilities.py) on a Biogrid object
"""
import urllib.request
import os
import json
from check_utilities import SrcClass, compare_versions
from mitab_utilities import table
import config_utilities as cf

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Biogrid(args)

class Biogrid(SrcClass):
    """Extends SrcClass to provide biogrid specific check functions.

    This Biogrid class provides source-specific functions that check the
    biogrid version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Biogrid with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'biogrid'
        url_base = ('http://thebiogrid.org/downloads/archives/'
                    'Latest%20Release/BIOGRID-ALL-LATEST.mitab.zip')
        aliases = {"PPI": "PPI"}
        super(Biogrid, self).__init__(name, url_base, aliases, args)
        self.access_key = '2fe900033b39209b8f63d531fcb24790'
        self.chunk_size = 50000
        src_data_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
        sp_dir = os.path.join(src_data_dir, 'species', 'species.json')
        sp_dict = json.load(open(sp_dir))
        self.taxid_list = sp_dict.values()

        self.source_url = "https://thebiogrid.org/"
        self.image = "https://pbs.twimg.com/profile_images/875385819422437376/HQv1quNo_400x400.jpg"
        self.reference = ("Chatr-aryamontri A, Oughtred R, Boucher L, et al. The BioGRID "
                          "interaction database: 2017 update. Nucleic Acids Res. "
                          "2017;45(D1):D369-D379.")
        self.pmid = 27980099
        self.license = ('BioGRID interaction data are 100% freely available to both commercial and '
                        'academic users.')

    def get_source_version(self, alias):
        """Return the release version of the remote biogrid:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Biogrid, self).get_source_version(alias)
        if version == 'unknown':
            url = 'http://webservice.thebiogrid.org/version?accesskey='
            response = urllib.request.urlopen(url + self.access_key)
            self.version[alias] = response.read().decode()
            response.close()
            for alias_name in self.aliases:
                self.version[alias_name] = self.version[alias]
            return self.version[alias]
        return version

    def table(self, raw_line, version_dict):
        """Uses the provided raw_line file to produce a table file, an
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
    """Runs compare_versions (see utilities.compare_versions) on a biogrid
    object

    This runs the compare_versions function on a biogrid object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in biogrid.
    """
    compare_versions(Biogrid())

if __name__ == "__main__":
    main()
