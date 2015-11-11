"""Extension of utilities.py to provide functions required to check the
version information of reactome and determine if it needs to be updated.

Classes:
    Reactome: Extends the SrcClass class and provides the static variables and
        reactome specific functions required to perform a check on reactome.

Functions:
    get_SrcClass: returns a Reactome object
    main: runs compare_versions (see utilities.py) on a Reactome object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import os
import json
import hashlib
import csv
import config_utilities as cf
import table_utilities as tu

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Reactome(args)

class Reactome(SrcClass):
    """Extends SrcClass to provide reactome specific check functions.

    This Reactome class provides source-specific functions that check the
    reactome version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Reactome with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'reactome'
        url_base = 'http://www.reactome.org/'
        aliases = {"Ensembl2Reactome_All_Levels": "genes2pathways",
                   "ReactomePathways": "reactomePathways",
                   "homo_sapiens.interactions": "pathwayInteractions",
                   "ReactomePathwaysRelation":"ReactomeRelations"}
        super(Reactome, self).__init__(name, url_base, aliases, args)

    def get_source_version(self, alias):
        """Return the release version of the remote reactome:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Reactome, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'category/reactome-announcement/'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r'Version (\d+)', d_line)
                if match is not None:
                    response.close()
                    self.version[alias] = match.group(1)
                    break
            for alias_name in self.aliases:
                self.version[alias_name] = match.group(1)
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
        return super(Reactome, self).get_local_file_info(alias)

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
        return super(Reactome, self).get_remote_file_size(url)

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
        return super(Reactome, self).get_remote_file_modified(url)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        url = self.url_base + 'download/current/'
        if 'interactions' in alias:
            url += alias + '.txt.gz'
        else:
            url += alias + '.txt'
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
        maps = {"Ensembl2Reactome_All_Levels": False,
                "ReactomePathways": True,
                "homo_sapiens.interactions": False,
                "ReactomePathwaysRelation": True}
        return maps[alias]

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
        dependencies = {"Ensembl2Reactome_All_Levels": ['ReactomePathways'],
                        "ReactomePathways": list(),
                        "homo_sapiens.interactions": list(),
                        "ReactomePathwaysRelation": ['ReactomePathways']}
        return dependencies[alias]

    def create_mapping_dict(self, filename):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in mapping reactome pathway nodes
        from the file specified by filetype. If the alias is
        Ensembl2Reactome_All_Levels it uses the second column as the key and
        the first column as the value, otherwise it creates a dictionary using
        the first column as the key and the second column as the value.

        Args:
            filename(str): The name of the file containing the information
                needed to produce the maping dictionary.

        Returns:
            dict: A dictionary for use in mapping nodes or edge types.
        """
        return super(Reactome, self).create_mapping_dict(filename)

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

        alias = version_dict['alias']

        #outfiles
        table_file = rawline.replace('rawline', 'edge')
        n_meta_file = rawline.replace('rawline', 'node_meta')
        e_meta_file = rawline.replace('rawline', 'edge_meta')

        if alias == 'Ensembl2Reactome_All_Levels':

            #static column values
            n1type = 'property'
            n1spec = '0'
            n2type = 'gene'
            n2hint = 'Ensembl_GeneID'
            score = 1
            info_type = 'alt_alias'
            info_type1 = 'link'
            info_type2 = 'evidence'

            #mapping files
            pathway = os.path.join('..', 'ReactomePathways', 'reactome.ReactomePathways.json')
            with open(pathway) as infile:
                path_map = json.load(infile)
            species = (os.path.join('..', '..', 'species', 'species_map',\
                    'species.species_map.json'))
            with open(species) as infile:
                species_map = json.load(infile)

            with open(rawline, encoding='utf-8') as infile, \
                open(table_file, 'w') as edges,\
                open(n_meta_file, 'w') as n_meta,\
                open(e_meta_file, 'w') as e_meta:
                edge_writer = csv.writer(edges, delimiter='\t')
                n_meta_writer = csv.writer(n_meta, delimiter='\t')
                e_meta_writer = csv.writer(e_meta, delimiter='\t')
                for line in infile:
                    line = line.replace('"', '').strip().split('\t')
                    if len(line) == 1:
                        continue
                    chksm = line[2]
                    raw = line[3:]
                    n1_orig_id = raw[1]
                    n1_mapped = path_map.get(n1_orig_id, "unmapped:no-name::unmapped")
                    (n1_id, n1hint) = n1_mapped.split('::')
                    n1_link = raw[2]

                    n2_id = raw[0]
                    n2spec_str = raw[5]
                    n2spec = species_map.get(n2spec_str, "unmapped:unsupported-species")

                    e_meta = raw[4]
                    et_hint = "reactome_curated"
                    if e_meta == "IEA":
                        et_hint = "reactome_inferred"
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1_id, n1hint, n1type, n1spec,\
                                             n2_id, n2hint, n2type, n2spec, et_hint,
                                             str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1_id, n1hint, n1type, n1spec, \
                        n2_id, n2hint, n2type, n2spec, et_hint, score, t_chksum])
                    n_meta_writer.writerow([chksm, n1_id, info_type1, n1_link])
                    e_meta_writer.writerow([chksm, info_type2, e_meta])
            outfile = e_meta_file.replace('edge_meta','unique_edge_meta')
            tu.csu(e_meta_file, outfile)
            outfile = n_meta_file.replace('node_meta','unique_node_meta')
            tu.csu(n_meta_file, outfile)
        if alias == 'homo_sapiens.interactions':

            #static column values
            n1type = 'gene'
            n1spec = '9606'
            n2type = 'gene'
            n2spec = '9606'
            score = 1
            info_type = 'detail'
            info_type1 = 'reference'

            #mapping files

            with open(rawline, encoding='utf-8') as infile, \
                open(table_file, 'w') as edges,\
                open(e_meta_file, 'w') as e_meta:
                edge_writer = csv.writer(edges, delimiter='\t')
                e_meta_writer = csv.writer(e_meta, delimiter='\t')
                for line in infile:
                    line = line.replace('"', '').strip().split('\t')
                    if len(line) == 1:
                        continue
                    chksm = line[2]
                    raw = line[3:]

                    # skip commented lines
                    comment_match = re.match('#', raw[0])
                    if comment_match is not None:
                        continue

                    n1_str = raw[0]
                    n1hint = n1_str.split(':', 1)[0]
                    n1_id = n1_str.split(':', 1)[1]
                    n2_str = raw[3]
                    n2hint = n2_str.split(':', 1)[0]
                    if n2hint == "": continue
                    n2_id = n2_str.split(':', 1)[1]

                    et_str = raw[6]
                    et_hint = 'reactome_PPI_' + et_str

                    detail_str = raw[7]
                    ref_str = raw[8]
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1_id, n1hint, n1type, n1spec,\
                                             n2_id, n2hint, n2type, n2spec, et_hint,
                                             str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1_id, n1hint, n1type, n1spec, \
                        n2_id, n2hint, n2type, n2spec, et_hint, score, t_chksum])
                    e_meta_writer.writerow([chksm, info_type, detail_str])
                    e_meta_writer.writerow([chksm, info_type1, ref_str])
            outfile = e_meta_file.replace('edge_meta','unique_edge_meta')
            tu.csu(e_meta_file, outfile)



if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Reactome
    object

    This runs the compare_versions function on a Reactome object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Reactome.
    """
    compare_versions(Reactome())
