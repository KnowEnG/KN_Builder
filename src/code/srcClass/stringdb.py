"""Extension of utilities.py to provide functions required to check the
version information of stringdb and determine if it needs to be updated.

Classes:
    Stringdb: Extends the SrcClass class and provides the static variables and
        stringdb specific functions required to perform a check on stringdb.

Functions:
    get_SrcClass: returns a Stringdb object
    main: runs compare_versions (see utilities.py) on a Stringdb object
"""
import urllib.request
import re
import os
import hashlib
import csv
import json
import requests
import config_utilities as cf
import fetch_utilities as fu
import table_utilities as tu
from check_utilities import SrcClass, compare_versions


def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Stringdb(args)

class Stringdb(SrcClass):
    """Extends SrcClass to provide stringdb specific check functions.

    This Stringdb class provides source-specific functions that check the
    stringdb version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Stringdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'stringdb'
        url_base = 'https://string-db.org/'
        aliases = dict()
        super(Stringdb, self).__init__(name, url_base, aliases, args)
        self.aliases = self.get_aliases(args)
        self.chunk_size = 250000

        self.source_url = "https://string-db.org/"
        self.image = "http://meringlab.org/logos/string.png"
        self.reference = ("Szklarczyk D, Franceschini A, Wyder S, et al. STRING v10: "
                          "protein-protein interaction networks, integrated over the tree of life. "
                          "Nucleic Acids Res. 2015;43(Database issue):D447-52.")
        self.pmid = 25352553
        self.license = ('The dataset obtained from STRING is distributed under '
                        'Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)')

    def get_aliases(self, args=cf.config_args()):
        """Helper function for producing the alias dictionary.

        This returns a dictionary where alias names are keys and alias info
        are the values. This helper function usse the species
        specific information for the build of the Knowledge Network, which is
        produced by ensembl.py during setup utilities and is located at
        cf.DEFAULT_MAP_PATH/species/species.json, in order to fetch all matching
        species specific aliases from the source.

        Args:
            args (Namespace): args as populated namespace or 'None' for defaults

        Returns:
            dict: A dictionary of species:(taxid, division) values
        """
        src_data_dir = os.path.join(args.working_dir, args.data_path, cf.DEFAULT_MAP_PATH)
        sp_dir = os.path.join(src_data_dir, 'species', 'species.json')
        sp_dict = json.load(open(sp_dir))
        alias_dict = dict()
        for species, taxid in sp_dict.items():
            species = species.capitalize().replace('_', ' ')
            sp_abbrev = species[0] + species.split(' ')[1][:3]
            url = self.get_remote_url(taxid)
            req = requests.get(url)
            if req.status_code == 200:
                alias_dict[taxid] = sp_abbrev
            else:
                print("warning: string species {} error {}".format(taxid, req.status_code))
        return alias_dict

    def get_source_version(self, alias):
        """Return the release version of the remote stringdb:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        if alias not in self.version:
            response = fu.opener.open(self.url_base)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search("string_database_version_dotted: '(\d+\.?\d*)'", d_line)
                if match is not None:
                    response.close()
                    vers = match.group(1)
                    if '.' in vers:
                        vers = vers.rstrip('0')
                    if vers[-1] == '.':
                        vers = vers[:-1]
                    self.version[alias] = vers
                    return self.version[alias]
        return self.version[alias]

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
        version = self.get_source_version(alias)
        url = self.url_base + 'download/protein.links.detailed.v'
        url += version + '/' + alias + '.protein.links.detailed.v'
        url += version + '.txt.gz'
        return url

    def table(self, raw_line, version_dict):
        """Uses the provided raw_line file to produce a 2table_edge file, an
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
            raw_line(str): The path to the raw_line file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """

        #outfiles
        table_file = raw_line.replace('raw_line', 'table')
        #n_meta_file = raw_line.replace('raw_line', 'node_meta')
        e_meta_file = raw_line.replace('raw_line', 'edge_meta')

        #static column values
        n1type = 'gene'
        n1hint = 'unknown'
        n2type = 'gene'
        n2hint = 'unknown'
        info_type = 'combined_score'
        edge_types = {2: 'STRING_neighborhood',
                      3: 'STRING_fusion',
                      4: 'STRING_cooccurence',
                      5: 'STRING_coexpression',
                      6: 'STRING_experimental',
                      7: 'STRING_database',
                      8: 'STRING_textmining'}

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(e_meta_file, 'w') as e_meta:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            e_meta_writer = csv.writer(e_meta, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if line[1] == '1':
                    continue
                chksm = line[0]
                raw = line[3].split(' ')
                n1list = raw[0].split('.')
                n2list = raw[1].split('.')
                if len(n1list) < 2 or len(n2list) < 2:
                    continue
                n1spec = n1list[0]
                n1id = '.'.join(n1list[1:])
                n2spec = n2list[0]
                n2id = '.'.join(n2list[1:])
                for ety in edge_types:
                    et_hint = edge_types[ety]
                    score = raw[ety]
                    if score == '0':
                        continue
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1id, n1hint, n1type, n1spec,
                                             n2id, n2hint, n2type, n2spec, et_hint,
                                             str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1id, n1hint, n1type, n1spec,
                                          n2id, n2hint, n2type, n2spec, et_hint,
                                          score, t_chksum])
                c_score = raw[9]
                e_meta_writer.writerow([chksm, info_type, c_score])
        outfile = e_meta_file.replace('edge_meta', 'unique_edge_meta')
        tu.csu(e_meta_file, outfile, [1, 2, 3])


def main():
    """Runs compare_versions (see utilities.compare_versions) on a Stringdb
    object

    This runs the compare_versions function on a Stringdb object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Stringdb.
    """
    compare_versions(Stringdb())

if __name__ == "__main__":
    main()
