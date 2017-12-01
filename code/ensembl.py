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
import ftplib
import json
import urllib.request
import re
import time
import os
import shutil
import mysql.connector
from check_utilities import SrcClass, compare_versions
import config_utilities as cf
from fetch_utilities import download
import mysql_utilities as db
import redis_utilities as ru

TABLE_LIST = ['external_db', 'gene', 'object_xref', 'transcript',
              'translation', 'xref']

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Ensembl(args)

def fetch(version_dict, args=cf.config_args()):
    """Fetches all mysql tables and syntax for alias described by version_json.

    This takes the path to a version_json (source.alias.json) and downloads
    all relevant tables (see fetch_utilites.download).

    Args:
        version_dict (dict): version dictionary describing the source:alias
        args: populated namespace from argparse

    Returns:
    """
    shutil.move(download(version_dict), 'schema.sql')
    base_url = version_dict['remote_url']
    base_url = base_url[:base_url.rfind('/') + 1]
    for table in TABLE_LIST:
        version_dict['remote_url'] = base_url + table + '.txt.gz'
        shutil.move(download(version_dict), table + '.txt')
    try:
        db_import(version_dict, args)
    except mysql.connector.DatabaseError as err:
        print('Encountered error: ' + str(err))
        print('Trying operation again')
        db_import(version_dict, args)
    except:
        raise

def db_import(version_dict, args=cf.config_args()):
    """Imports the data into the database and saves local id mapping
    dictionaries.

    This takes the version dictionary (source.alias.json) and imports all
    relevant tables into the database. It then combines all the relevant tables
    for gene id mapping, and saves local copies of the mapping dictionaries.

    Args:
        version_json (dict): path to the version dictionary describing the
            source:alias

    Returns:
    """
    db.import_ensembl(version_dict['alias'], args)
    db.combine_tables(version_dict['alias'], args)
    db.query_all_mappings(version_dict, args)
    node_table = db.import_nodes(version_dict, args)
    ru.import_gene_nodes(node_table, args)
    ru.import_ensembl(version_dict['alias'], args)
    db_name = 'ensembl_' + version_dict['alias']
    mysql_db = db.get_database(db_name, args)
    mysql_db.drop_db(db_name)

def species_import(alias_dict, args=cf.config_args()):
    """Produces the species.txt file and imports it into the database. Also
    creates a species.json file.

    This takes the alias dictionary and creates the species table:
    taxon   sp_abbrev   sp_sciname  representative
    and imports the table into the database. It also produces a species.json
    file of the form species:taxid.

    Args:
        alias_dict (dict): alias dictionary describing the source

    Returns:
    """
    src_data_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
    table_dir = os.path.join(src_data_dir, 'species')
    os.makedirs(table_dir, exist_ok=True)
    table_file = os.path.join(table_dir, 'species.txt')
    species_file = table_file.replace('txt', 'json')
    species_dict = dict()
    if os.path.isfile(species_file):
        os.remove(species_file)
    #    previous_species = json.load(open(species_file))
    #    species_dict.update(previous_species)
    with open(table_file, 'a') as sp_file:
        for species in alias_dict:
            taxid = alias_dict[species].split('::')[0]
            species = species.capitalize().replace('_', ' ')
            species_dict[species] = taxid
            sp_abbrev = species[0] + species.split(' ')[1][:3]
            sp_file.write('\t'.join([taxid, sp_abbrev, species, species])+'\n')
    db.get_database(None, args).import_table('KnowNet', table_file, '--ignore')
    with open(species_file, 'w') as outfile:
        json.dump(species_dict, outfile, indent=4, sort_keys=True)


class Ensembl(SrcClass):
    """Extends SrcClass to provide ensembl specific check functions.

    This Ensembl class provides source-specific functions that check the
    ensembl version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Ensembl with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'ensembl'
        url_base = 'ftp.ensembl.org'
        self.reference = ''
        self.image = ''
        self.source_url = ''
        self.pmid = 0
        self.license = ''
        aliases = self.get_aliases(args)
        super(Ensembl, self).__init__(name, url_base, aliases, args)
        rem_aliases = list()
        for alias in self.aliases:
            if not self.get_remote_url(alias):
                print('Ensembl does not have a core SQL db for ' + alias)
                rem_aliases.append(alias)
        for alias in rem_aliases:
            self.aliases.pop(alias)
        args.ens_species = ',,'.join(aliases.keys())
        species_import(self.aliases, args)

    def get_aliases(self, args=cf.config_args()):
        """Return the alias dictionary for ensembl based on the provided alias_list.

        This returns a dictionary where species names are keys and a tuple of
        taxid and ensembl division are values. The species name serves as the
        alias and the tuple serves as the alias information.

        Args:
            args (Namespace): args as populated namespace or 'None' for defaults

        Returns:
            dict: A dictionary of species:(taxid, division) values
        """
        #replace all special keywords
        alias_list = args.ens_species
        all_species = 'REPRESENTATIVE,,BACTERIA,,FUNGI,,METAZOA,,PLANTS,,PROTISTS,,VERTEBRATES'
        representative = ('mus_musculus,,arabidopsis_thaliana,,saccharomyces_cerevisiae,,'
                          'caenorhabditis_elegans,,drosophila_melanogaster,,homo_sapiens')
        research = ('arabidopsis_thaliana,,caenorhabditis_elegans,,drosophila_melanogaster,,'
                    'homo_sapiens,,mus_musculus,,saccharomyces_cerevisiae,,bos_taurus,,sus_scrofa,,'
                    'pan_troglodytes,,taeniopygia_guttata,,daphnia_pulex,,xenopus_tropicalis,,'
                    'macaca_mulatta,,rattus_norvegicus,,apis_mellifera,,danio_rerio,,'
                    'gallus_gallus,,gasterosteus_aculeatus,,aedes_aegypti,,canis_familiaris')
        keywords = {'ALL':all_species,
                    'REPRESENTATIVE':representative,
                    'BACTERIA':'EnsemblBacteria',
                    'FUNGI':'EnsemblFungi',
                    'METAZOA':'EnsemblMetazoa',
                    'PLANTS':'EnsemblPlants',
                    'PROTISTS':'EnsemblProtists',
                    'VERTEBRATES':'Ensembl'}
        alias_list = alias_list.replace('ALL', all_species)
        alias_list = alias_list.replace('REPRESENTATIVE', representative)
        alias_list = alias_list.replace('RESEARCH', research)
        species_list = alias_list.split(',,')
        alias_dict = dict()
        for species in species_list: #replace keywords
            print('Finding Aliases for {0}'.format(species))
            if species.upper() in keywords:
                division = keywords[species.upper()]
                if division == 'Ensembl':
                    rest_url = 'http://rest.ensembl.org'
                    url_base = 'ftp.ensembl.org'
                elif division == 'EnsemblBacteria':
                    print('Bacterial species are unsupported')
                    continue
                else:
                    rest_url = 'http://rest.ensemblgenomes.org'
                    url_base = 'ftp.ensemblgenomes.org'
                query = '/info/species?content-type=application/json;division='
                query += division
                response = urllib.request.urlopen(rest_url + query)
                json_obj = json.loads(response.read().decode())
                sp_list = json_obj['species']
                for sp in sp_list:
                    species_name = sp['name']
                    rest_url = 'http://rest.ensemblgenomes.org'
                    query = '/info/genomes/{0}?content-type=application/json'
                    query = query.format(species_name)
                    response = urllib.request.urlopen(rest_url + query)
                    json_obj = json.loads(response.read().decode())
                    taxid = json_obj['species_taxonomy_id']
                    alias_dict[species_name] = '::'.join([taxid, url_base, division])
            else:
                rest_url = 'http://rest.ensemblgenomes.org'
                query = '/info/genomes/{0}?content-type=application/json'
                query = query.format(species)
                response = urllib.request.urlopen(rest_url + query)
                json_obj = json.loads(response.read().decode())
                division = json_obj['division']
                if division == 'Ensembl':
                    url_base = 'ftp.ensembl.org'
                elif division == 'EnsemblBacteria':
                    print('Bacterial species are unsupported')
                    continue
                else:
                    url_base = 'ftp.ensemblgenomes.org'
                taxid = json_obj['species_taxonomy_id']
                alias_dict[species] = '::'.join([taxid, url_base, division])
        print('Found {0} aliases'.format(len(alias_dict)))
        return alias_dict

    def get_source_version(self, alias):
        """Return the release version of the remote ensembl:alias.

        This returns the release version of the remote source for a specific
        alias. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        url_base = self.aliases[alias].split('::')[1]
        if 'ensemblgenomes' in url_base:
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
        (taxid, url, division) = self.aliases[alias].split('::')
        division = division.replace('Ensembl', '').lower()
        if division:
            chdir = '/pub/current/{0}/mysql/'.format(division)
        else:
            chdir = '/pub/current_mysql/'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        file_size = 0
        file_dir = ''
        for directory in ftp.nlst():
            match = re.match(alias + r'_core_[\S]*', directory)
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
        (taxid, url, division) = self.aliases[alias].split('::')
        division = division.replace('Ensembl', '').lower()
        if division:
            chdir = '/pub/current/{0}/mysql/'.format(division)
        else:
            chdir = '/pub/current_mysql/'
        chk_file = '/CHECKSUMS'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        for directory in ftp.nlst():
            match = re.match(alias + r'_core_[\S]*', directory)
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
        (taxid, url, division) = self.aliases[alias].split('::')
        division = division.replace('Ensembl', '').lower()
        if division:
            chdir = '/pub/current/{0}/mysql/'.format(division)
        else:
            chdir = '/pub/current_mysql/'
        ftp = ftplib.FTP(url)
        ftp.login()
        ftp.cwd(chdir)
        file_dir = ''
        for directory in ftp.nlst():
            match = re.match(alias + r'_core_[\S]*', directory)
            if match is not None:
                file_dir = directory
                break
        for file in ftp.nlst(file_dir):
            if 'sql.gz' in file:
                return 'ftp://' + url + chdir + file
        return ''

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
        return True

if __name__ == "__main__":
    compare_versions(Ensembl())
