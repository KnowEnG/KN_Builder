"""Extension of utilities.py to provide functions required to check the
version information of ensembl and determine if it needs to be updated.

Classes:
    Ensembl: Extends the SrcClass class and provides the static variables and
        ensembl specific functions required to process ensembl.

Functions:
    get_SrcClass: returns an Ensembl object
    fetch: performs a fetch for ensembl
    main: runs compare_versions (see utilities.py) on a Ensembl object

Variables:
    TABLE_LIST: list of tables of interest from Ensembl
"""
from check_utilities import SrcClass, compare_versions
from fetch_utilities import download
import mysql_utilities as db
import ftplib
import json
import urllib.request
import re
import time
import shutil

TABLE_LIST = ['external_db', 'gene', 'object_xref', 'transcript',
            'translation', 'xref']

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Ensembl()

def fetch(version_dict):
    """Fetches all mysql tables and syntax for alias described by version_json.

    This takes the path to a version_json (source.alias.json) and downloads
    all relevant tables (see fetch_utilites.download).

    Args:
        version_dict (dict): version dictionary describing the source:alias

    Returns:
    """
    shutil.move(download(version_dict), 'schema.sql')
    base_url = version_dict['remote_url']
    base_url = base_url[:base_url.rfind('/') + 1]
    for table in TABLE_LIST:
        version_dict['remote_url'] = base_url + table + '.txt.gz'
        shutil.move(download(version_dict), table + '.txt')

def db_import(version_json):
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    db.import_ensembl(version_dict['alias'])
    db.combine_tables(version_dict['alias'])
    db.create_mapping_dicts(version_dict['alias'])

class Ensembl(SrcClass):
    """Extends SrcClass to provide ensembl specific check functions.

    This Ensembl class provides source-specific functions that check the
    ensembl version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
        """Init a Ensembl with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'ensembl'
        url_base = 'ftp.ensembl.org'
        aliases = { "mus_musculus": "",
                    "arabidopsis_thaliana": "",
                    "saccharomyces_cerevisiae": "",
                    "caenorhabditis_elegans": "",
                    "drosophila_melanogaster": "",
                    "homo_sapiens": ""}
        super(Ensembl, self).__init__(name, url_base, aliases)
        self.url_base_plants = 'ftp.ensemblgenomes.org'

    def get_source_version(self, alias):
        """Return the release version of the remote ensembl:alias.

        This returns the release version of the remote source for a specific
        alias. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        if alias == 'arabidopsis_thaliana':
            rest_url = 'http://rest.ensemblgenomes.org'
            query = '/info/eg_version/?content-type=application/json'
            key = 'version'
        else:
            rest_url = 'http://rest.ensembl.org'
            query = '/info/data/?content-type=application/json'
            key = 'releases'
        response = urllib.request.urlopen(rest_url + query)
        json_obj = json.loads(response.read().decode())
        version = str(json_obj[key])
        if '[' in version:
            version = version[1:-1]
        return version

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        (See check_utilities.get_local_file_info)

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        return super(Ensembl, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This builds a url for the given alias (see get_remote_url) and then
        calculates the file size of the directory by summing the size of all
        the files it contains.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        if alias == 'arabidopsis_thaliana':
            url = self.url_base_plants
            chdir = '/pub/current/plants/mysql/'
        else:
            url = self.url_base
            chdir = '/pub/current_mysql/'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        file_size = 0
        file_dir = ''
        for directory in ftp.nlst():
            match = re.match(alias + '_core_[\S]*', directory)
            if match is not None:
                file_dir = directory
                break
        for file in ftp.nlst(file_dir):
            ftp.voidcmd('TYPE I')
            file_size += ftp.size(file)
        ftp.quit()
        return file_size

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This builds a url for the given alias (see get_remote_url) and then
        gets the file modified date of the remote CHECKSUMS file (assumed to
        be roughly the same date for all files corresponding to the alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        if alias == 'arabidopsis_thaliana':
            url = self.url_base_plants
            chdir = '/pub/current/plants/mysql/'
            chk_file = '/CHECKSUMS'
        else:
            url = self.url_base
            chdir = '/pub/current_mysql/'
            chk_file = '/CHECKSUMS.gz'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        for directory in ftp.nlst():
            match = re.match(alias + '_core_[\S]*', directory)
            if match is not None:
                time_str = ftp.sendcmd('MDTM ' + match.group(0) + chk_file)
                time_str = time_str[4:]
                time_format = "%Y%m%d%H%M%S"
                ftp.quit()
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
        if alias == 'arabidopsis_thaliana':
            url = self.url_base_plants
            chdir = '/pub/current/plants/mysql/'
        else:
            url = self.url_base
            chdir = '/pub/current_mysql/'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        file_dir = ''
        for directory in ftp.nlst():
            match = re.match(alias + '_core_[\S]*', directory)
            if match is not None:
                file_dir = directory
                break
        for file in ftp.nlst(file_dir):
            if 'sql.gz' in file:
                return 'ftp://' + url + chdir + file

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
        return super(Ensembl, self).is_map(alias)

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
        return super(Ensembl, self).get_dependencies(alias)

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
        return super(Ensembl, self).create_mapping_dict(filename)

    def table(self, rawline, version_dict):
        """Uses the provided raw_lines file to produce a 2table_edge file, an
        edge_meta file, and a node_meta file (only for property nodes).

        This returns noting but produces the 2table formatted files from the
        provided raw_lines file:
            raw_lines table (file, line num, line_chksum, rawline)
            2tbl_edge table (line_cksum, n1name, n1hint, n1type, n1spec, 
                            n2name, n2hint, n2type, n2spec, et_hint, score)
            edge_meta (line_cksum, info_type, info_desc)
            node_meta (line_cksum, node_num (1 or 2), 
                       info_type (evidence, relationship, experiment, or link),
                       info_desc (text))
        By default this function does nothing (must be overridden)

        Args:
            rawline(str): The path to the raw_lines file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """
        return table(rawline, version_dict)

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a ensembl
    object if no 

    This runs the compare_versions function on a ensembl object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in ensembl.
    """
    compare_versions(Ensembl())
