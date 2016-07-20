"""Extension of utilities.py to provide functions required to check the
version information of biogrid and determine if it needs to be updated.

Classes:
    Biogrid: Extends the SrcClass class and provides the static variables and
        biogrid specific functions required to perform a check on biogrid.

Functions:
    get_SrcClass: returns a Biogrid object
    main: runs compare_versions (see utilities.py) on a Biogrid object
"""
from check_utilities import SrcClass, compare_versions
from mitab_utilities import table
import urllib.request
import config_utilities as cf
import os
import json

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
        return super(Biogrid, self).get_local_file_info(alias)

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
        return super(Biogrid, self).get_remote_file_size(url)

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
        return super(Biogrid, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        (See utilities.SrcClass.get_remote_url)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        return super(Biogrid, self).get_remote_url(alias)

    def is_map(self, alias):
        """Return a boolean representing if the provided alias is used for
        source specific mapping of nodes or edges.

        This returns a boolean representing if the alias corresponds to a file
        used for mapping. By default this returns True if the alias ends in
        '_map' and False otherwise.

        Args:
            alias(str): An alias defined in self.aliases.

        Returns:
            bool: Whether or not the alias is used for mapping.
        """
        return super(Biogrid, self).is_map(alias)

    def get_dependencies(self, alias):
        """Return a list of other aliases that the provided alias depends on.

        This returns a list of other aliases that must be processed before
        full processing of the provided alias can be completed.

        Args:
            alias(str): An alias defined in self.aliases.

        Returns:
            list: The other aliases defined in self.aliases that the provided
                alias depends on.
        """
        return super(Biogrid, self).get_dependencies(alias)

    def create_mapping_dict(self, filename):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in mapping nodes or edge types from
        the file specified by filetype. By default it opens the file specified
        by filename creates a dictionary using the first column as the key and
        the second column as the value.

        Args:
            filename(str): The name of the file containing the information
                needed to produce the maping dictionary.

        Returns:
            dict: A dictionary for use in mapping nodes or edge types.
        """
        return super(Biogrid, self).create_mapping_dict(filename)

    def table(self, raw_line, version_dict):
        """Uses the provided raw_line file to produce a table file, an
        edge_meta file, and a node_meta file (only for property nodes).

        This returns noting but produces the table formatted files from the
        provided raw_line file:
            raw_line (line_hash, line_num, file_id, raw_line)
            table_file (raw_line_cksum, n1name, n1hint, n1type, n1spec,
                        n2name, n2hint, n2type, n2spec, et_hint, score,
                        tableline_cksum)
            edge_meta (line_hash, info_type, info_desc)
            node_meta (node_id, 
                       info_type (evidence, relationship, experiment, or link), 
                       info_desc (text))

        Args:
            raw_line(str): The path to the raw_lines file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """
        return table(raw_line, version_dict, self.taxid_list)

if __name__ == "__main__":
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
