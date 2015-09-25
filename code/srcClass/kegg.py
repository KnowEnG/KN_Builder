"""Extension of utilities.py to provide functions required to check the
version information of kegg and determine if it needs to be updated.

Classes:
    Kegg: Extends the SrcClass class and provides the static variables and
        kegg specific functions required to perform a check on kegg.

Functions:
    get_SrcClass: returns a Kegg object
    main: runs compare_versions (see utilities.py) on a Kegg object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import time
import os
import json
import csv
import config_utilities as cf

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Kegg(args)

class Kegg(SrcClass):
    """Extends SrcClass to provide kegg specific check functions.

    This Kegg class provides source-specific functions that check the
    kegg version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Kegg with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'kegg'
        url_base = 'http://rest.kegg.jp/'
        aliases = {"pathway": "pathways",
                   "ath": "Arabidopsis thaliana",
                   "ath_map": "Atha_IDmap",
                   "cel": "Caenorhabditis elegans",
                   "cel_map": "Cele_IDmap",
                   "dme": "Drosophila melanogaster",
                   "dme_map": "Dmel_IDmap",
                   "hsa": "Homo sapiens",
                   "hsa_map": "Hsap_IDmap",
                   "mmu": "Mus musculus",
                   "mmu_map": "Mmus_IDmap",
                   "sce": "Saccharomyces cerevisiae",
                   "sce_map": "Scer_IDmap"}
        super(Kegg, self).__init__(name, url_base, aliases, args)
        self.date_modified = 'unknown'

    def get_source_version(self, alias):
        """Return the release version of the remote kegg:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias and is 'unknown' in
        this case. This value is stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Kegg, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'info/pathway'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'Release (\S+), ([^<\n]*)', d_line)
                if match is not None:
                    self.version[alias] = match.group(1)
                    response.close()
                    break
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
        return super(Kegg, self).get_local_file_info(alias)

    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This returns -1.0 because the remote file size is not returned by the
        REST server.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            int: The remote file size in bytes.
        """
        return -1

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the remote file date modifed as specificied by the version
        information page.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        if self.date_modified == 'unknown':
            url = self.url_base + 'info/pathway'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'Release (\S+), ([^<\n]*)', d_line)
                if match is not None:
                    time_str = match.group(2)
                    response.close()
                    break
            time_format = "%b %y"
            date_modified = time.mktime(time.strptime(time_str, time_format))
            self.date_modified = date_modified
        return self.date_modified

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the alias and url_base.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        if 'map' in alias:
            url = self.url_base + 'conv/ncbi-geneid/' + alias[:-4]
        elif alias == 'pathway':
            url = self.url_base + 'list/pathway'
        else:
            url = self.url_base + 'link/pathway/' + alias
        return url
        
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
        if alias == 'pathway':
            return True
        else:
            return super(Kegg, self).is_map(alias)

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
        if alias[-4:] == '_map' or alias == 'pathway':
            return list()
        else:
            return [alias + '_map', 'pathway']

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
        return super(Kegg, self).create_mapping_dict(filename)

    def table(self, rawline, version_dict):
        """Uses the provided rawline file to produce a 2table_edge file, an
        edge_meta file, and a node_meta file (only for property nodes).

        This returns noting but produces the 2table formatted files from the
        provided rawline file:
            rawline table (file, line num, line_chksum, rawline)
            2tbl_edge table (line_cksum, n1name, n1hint, n1type, n1spec,
                            n2name, n2hint, n2type, n2spec, et_hint, score)
            edge_meta (line_cksum, info_type, info_desc)
            node_meta (line_cksum, node_num (1 or 2),
                       info_type (evidence, relationship, experiment, or link),
                       info_desc (text))

        Args:
            rawline(str): The path to the rawline file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """

        #outfiles
        table_file = rawline.replace('rawline','edge')
        n_meta_file = rawline.replace('rawline','node_meta')
        #e_meta_file = rawline.replace('rawline','edge_meta')

        #static column values
        n1type = 'property'
        n2type = 'gene'
        score = 1
        node_num = 1
        info_type = 'synonym'
        alias = version_dict['alias']

        #mapping files
        pathway = os.path.join('..', 'pathway', 'kegg.pathway.json')
        with open(pathway) as infile:
            path_map = json.load(infile)
        a_map = alias + '_map'
        alias_map = os.path.join('..', a_map, 'kegg.' + a_map + '.json')
        with open(alias_map) as infile:
            node_map = json.load(infile)
        species = (os.path.join('..', '..', 'species', 'species_map',\
                    'species.species_map.json'))
        with open(species) as infile:
           species_map = json.load(infile)

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(n_meta_file, 'w') as n_meta:
            reader = csv.reader(infile, delimiter='\t')
            edge_writer = csv.writer(edges, delimiter='\t')
            n_meta_writer = csv.writer(n_meta, delimiter='\t')
            for line in reader:
                chksm = line[2]
                raw = line[3:]
                n1_ID = raw[0]
                n1_orig_name = path_map.get(n1_ID.replace(':' + alias, \
                    ':map'), "unmapped:no-name")
                n1 = 'kegg_' + re.sub('[^a-zA-Z0-9]','_',n1_orig_name)[0:35]
                n1spec = '0'
                n1hint = 'kegg_pathway'
                n2_raw = raw[1]
                n2hint, n2 = node_map.get(n2_raw, \
                    "unmapped:unsupported-species").split(':')
                n2spec = species_map.get(version_dict['alias_info'], \
                    "unmapped:unsupported-species")
                et_hint = 'kegg_pathway'
                edge_writer.writerow([chksm, n1, n1hint, n1type, n1spec, \
                    n2, n2hint, n2type, n2spec, et_hint, score])
                n_meta_writer.writerow([chksm, info_type, n1_orig_name])

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a kegg
    object

    This runs the compare_versions function on a kegg object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in kegg.
    """
    compare_versions(Kegg())
