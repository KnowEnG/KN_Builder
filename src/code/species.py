"""Extension of utilities.py to provide functions required to check the
version information of species and determine if it needs to be updated.

Classes:
    Species: Extends the SrcClass class and provides the static variables and
        species specific functions required to perform a check on species.

Functions:
    get_SrcClass: returns an Species object
    main: runs compare_versions (see utilities.py) on a Species object
"""
import time
import ftplib
import csv
import json
import config_utilities as cf
from check_utilities import SrcClass, compare_versions

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Species(args)

class Species(SrcClass):
    """Extends SrcClass to provide species specific check functions.

    This Species class provides source-specific functions that check the
    species version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Species with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'species'
        url_base = 'ftp.ncbi.nih.gov'
        aliases = {"species_map": "mapping file for species"}
        super(Species, self).__init__(name, url_base, aliases, args)
        self.remote_file = 'names.dmp'

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see utilities.get_remote_file_size).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        ftp = ftplib.FTP(self.url_base)
        ftp.login()
        ftp.cwd('/pub/taxonomy/')
        ftp.voidcmd('TYPE I')
        file_size = ftp.size('taxdmp.zip')
        ftp.quit()
        return file_size

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This builds a url for the given alias (see get_remote_url) and then
        calls the SrcClass function (see utilities.get_remote_file_modified).

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        ftp = ftplib.FTP(self.url_base)
        ftp.login()
        ftp.cwd('/pub/taxonomy/')
        time_str = ftp.sendcmd('MDTM taxdmp.zip')
        time_str = time_str[4:]
        ftp.quit()
        time_format = "%Y%m%d%H%M%S"
        return time.mktime(time.strptime(time_str, time_format))

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
        url = self.url_base + '/pub/taxonomy/taxdmp.zip'
        return 'ftp://' + url

    def create_mapping_dict(self, filename, key_col=3, value_col=4):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in mapping species name to taxid from
        the file specified by filetype. Processes filetype by creating a
        dictionary of the scientific name, the unique name (which is the
        the scientific name unless this is not unique) and the 4 letter
        abbreviated name for each organism. This dictionary is written to disk
        as species.json and then returns a dictionary mapping taxid to species
        unique name.

        Args:
            filename(str): The name of the file containing the information
                needed to produce the maping dictionary.

        Returns:
            dict: A dictionary for use in mapping nodes or edge types.
        """
        species = dict()
        species2taxid = dict()

        with open(filename, encoding='utf-8') as infile:
            reader = csv.reader((line.replace('\t|', '') for line in infile),
                                delimiter='\t', quoting=csv.QUOTE_NONE)
            for full_line in reader:
                line = full_line[3:]
                if line[3] == 'scientific name':
                    taxid = line[0]
                    sci_name = line[1]
                    uniq_name = line[2]
                    if uniq_name == '':
                        uniq_name = sci_name
                    if ' ' in sci_name:
                        abbr_name = sci_name[0] + sci_name[sci_name.find(' ') + 1:][:3]
                    else: abbr_name = sci_name[:4]
                    species[taxid] = dict()
                    species[taxid]['scientific_name'] = sci_name
                    species[taxid]['unique_name'] = uniq_name
                    species[taxid]['abbreviated_name'] = abbr_name
        with open('species.json', 'w') as outfile:
            json.dump(species, outfile, indent=4, sort_keys=True)
        for key in species:
            s_name = species[key]['unique_name']
            species2taxid[s_name] = key
        return species2taxid

def main():
    """Runs compare_versions (see utilities.compare_versions) on a species
    object

    This runs the compare_versions function on a species object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in species.
    """
    compare_versions(Species())

if __name__ == "__main__":
    main()
