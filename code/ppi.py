"""Extension of utilities.py to provide functions required to check the
version information of ppi and determine if it needs to be updated.

Classes:
    Ppi: Extends the SrcClass class and provides the static variables and
        ppi specific functions required to perform a check on ppi.

Functions:
    get_SrcClass: returns a Ppi object
    main: runs compare_versions (see utilities.py) on a ppi object
"""
from utilities import SrcClass, compare_versions
import urllib.request
import time

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Ppi()

class Ppi(SrcClass):
    """Extends SrcClass to provide ppi specific check functions.

    This Ppi class provides source-specific functions that check the
    ppi version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Ppi with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'ppi'
        url_base = ('http://psidev.cvs.sourceforge.net/viewvc/*checkout*/'
                    'psidev/psi/mi/rel25/data/psi-mi25.obo')
        aliases = {"obo_map": "map file for PPI edge tyeps"}
        super(Ppi, self).__init__(name, url_base, aliases)

    def get_source_version(self, alias):
        """Return the release version of the remote ppi:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Ppi, self).get_source_version(alias)
        if version == 'unknown':
            url = self.get_remote_url(alias)
            response = urllib.request.urlopen(url)
            for line in response:
                d_line = line.decode()
                if 'CVversion' in d_line:
                    self.version[alias] = d_line.split(' ')[2].strip()
                    break
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
        return super(Ppi, self).get_local_file_info(alias)

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
        return super(Ppi, self).get_remote_file_size(url)

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
        response = urllib.request.urlopen(url)
        time_str = ''
        for line in response:
            d_line = line.decode()
            if 'date: ' in d_line:
                time_str = d_line[6:].strip()
                break
        response.close()
        if time_str == '':
            return super(Ppi, self).get_remote_file_modified(url)
        else:
            time_format = "%m:%d:%Y %H:%M"
            return time.mktime(time.strptime(time_str, time_format))

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        (See utilities.SrcClass.get_remote_url)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        return super(Ppi, self).get_remote_url(alias)

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
        return super(Ppi, self).is_map(alias)

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
        return super(Ppi, self).get_dependencies(alias)

    def create_mapping_dict(self, filename):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in interaction types to PPI edgetypes
        from the file specified by filetype. This involves reading through the
        interaction files and collapsing the interaction tree to only represent
        the desired keys.

        Args:
            filename(str): The name of the file containing the information
                needed to produce the maping dictionary.

        Returns:
            dict: A dictionary for use in mapping edge types.
        """
        term_map = dict()
        term_is_bait = list()
        ID = ''
        parent = ''
        ixn_to_type = {'MI:0208':'PPI_genetic_interaction',
                       'MI:0403':'PPI_colocalization',
                       'MI:0407':'PPI_direct_interaction',
                       'MI:0914':'PPI_association',
                       'MI:0915':'PPI_physical_association'}
        desired_keys = ixn_to_type.keys()
        with open(filename) as infile:
            for line in infile:
                if line.startswith('[Term]'):
                    ID = ''
                    parent = ''
                if line.startswith('id:'):
                    ID = line.split(' ')[1].strip()
                if line.startswith('def:') and ID != '':
                    if 'bait' in line.lower():
                        term_is_bait.append(ID)
                if line.startswith('is_a'):
                    parent = line.split(' ')[1].strip()
                    if ID != '' and parent != '':
                        if ID in desired_keys:
                            term_map[ID] = ID
                        else:
                            term_map[ID] = parent
                        ID = ''
                        parent = ''

        #remap Additive Genetic Interaction to Genetic Interaction
        term_map['MI:0799'] = 'MI:0208'
        #remap Genetic Interference to Genetic Interaction
        term_map['MI:0254'] = 'MI:0208'
        #remap two-hybird to phyiscal association
        term_map['MI:0018'] = 'MI:0915'
        #make physical interaction its own parent
        term_map['MI:0218'] = 'MI:0218'
        rem_keys = list()
        for key in term_map:
            value = term_map[key]
            #collapse dictionary
            while value not in desired_keys:
                if value not in term_map or term_map[key] == term_map[value]:
                    value = term_map[key]
                    break
                term_map[key] = term_map[value]
                value = term_map[key]
            if value not in desired_keys:
                ##remap the obsolete physical interaction term
                if value == 'MI:0218':
                    if key in term_is_bait:
                        value = 'MI:0914'
                    else:
                        value = 'MI:0915'
                    term_map[key] = value
                ##remove keys that did not map to our desired edge types
                else:
                    rem_keys.append(key)
                    continue
            term_map[key] = ixn_to_type[value]
        for key in rem_keys:
            del term_map[key]
        return term_map

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a ppi
    object

    This runs the compare_versions function on a ppi object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in ppi.
    """
    compare_versions(Ppi())
