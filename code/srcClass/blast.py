"""Extension of utilities.py to provide functions required to check the
version information of blast and determine if it needs to be updated.

Classes:
    Blast: Extends the SrcClass class and provides the static variables and
        blast specific functions required to perform a check on blast.

Functions:
    get_SrcClass: returns a Blast object
    main: runs compare_versions (see utilities.py) on a Blast object
"""
import csv
import hashlib
import math
import os
import json
import requests
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
    return Blast(args)

class Blast(SrcClass):
    """Extends SrcClass to provide blast specific check functions.

    This Blast class provides source-specific functions that check the
    blast version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Blast with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'blast'
#        url_base = 'http://veda.cs.uiuc.edu/blast/'
#        aliases = {"mm9_Atha10": "10090_3702",
#                   "mm9_Scer64": "10090_4932",
#                   "mm9_Cele235": "10090_6239",
#                   "mm9_Dmel5": "10090_7227",
#                   "mm9_hg19": "10090_9606",
#                   "mm9_mm9": "10090_10090",
#                   "hg19_Atha10": "9606_3702",
#                   "hg19_Scer64": "9606_4932",
#                   "hg19_Cele235": "9606_6239",
#                   "hg19_Dmel5": "9606_7227",
#                   "hg19_hg19": "9606_9606",
#                   "Dmel5_Atha10": "7227_3702",
#                   "Dmel5_Scer64": "7227_4932",
#                   "Dmel5_Cele235": "7227_6239",
#                   "Dmel5_Dmel5": "7227_7227",
#                   "Cele235_Atha10": "6239_3702",
#                   "Cele235_Scer64": "6239_4932",
#                   "Cele235_Cele235": "6239_6239",
#                   "Scer64_Atha10": "4932_3702",
#                   "Scer64_Scer64": "4932_4932",
#                   "Atha10_Atha10": "3702_3702"}

        url_base = 'http://knowredis.knoweng.org:8082/'
        aliases = dict()
        super(Blast, self).__init__(name, url_base, aliases, args)
        self.aliases = self.get_aliases(args)
        self.sc_max = 100  # may want to load these
        self.sc_min = 2 # may want to load these

        self.source_url = "https://blast.ncbi.nlm.nih.gov/"
        self.image = "https://blast.ncbi.nlm.nih.gov/images/protein-blast-cover.png"
        self.reference = ("Altschul SF, Gish W, Miller W, Myers EW, Lipman DJ. Basic local "
                          "alignment search tool. J Mol Biol. 1990;215(3):403-10.")
        self.pmid = 2231712
        self.license = ('NCBI itself places no restrictions on the use or distribution of the data '
                        'contained therein. Nor do we accept data when the submitter has requested '
                        'restrictions on reuse or redistribution. Full disclaimer can be found <a '
                        'href="https://www.ncbi.nlm.nih.gov/home/about/policies/#data.">here</a>.')

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
            splower = species.lower().replace(' ', '_')
            url = self.get_remote_url(splower)
            req = requests.get(url)
            if req.status_code == 200:
                alias_dict[splower] = taxid
        return alias_dict

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
        url = self.url_base + alias + "_" + alias + '.out'
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
        #e_meta_file = raw_line.replace('raw_line', 'edge_meta')

        #static column values
        n1type = 'gene'
        n2type = 'gene'
        n1hint = 'ENSEMBL_STABLE_ID'
        n2hint = 'ENSEMBL_STABLE_ID'
        et_hint = 'blastp_homology'
        #node_num = 1
        #info_type = 'synonym'
        alias = version_dict['alias']

        n1spec = version_dict['alias_info']
        n2spec = version_dict['alias_info']

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]
                n1id = raw[0]
                n2id = raw[1]
                evalue = raw[12]
                evalue = float(evalue)
                score = self.sc_min
                if evalue == 0.0:
                    score = self.sc_max
                if evalue > 0.0:
                    score = round(-1.0*math.log10(evalue), 4)
                if score > self.sc_max:
                    score = self.sc_max
                if score < self.sc_min:
                    score = self.sc_min

                hasher = hashlib.md5()
                hasher.update('\t'.join([chksm, n1id, n1hint, n1type, n1spec,\
                    n2id, n2hint, n2type, n2spec, et_hint, str(score)]).encode())
                t_chksum = hasher.hexdigest()
                edge_writer.writerow([chksm, n1id, n1hint, n1type, n1spec, \
                        n2id, n2hint, n2type, n2spec, et_hint, score, t_chksum])


def main():
    """Runs compare_versions (see utilities.compare_versions) on a blast
    object

    This runs the compare_versions function on a blast object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in blast.
    """
    compare_versions(Blast())

if __name__ == "__main__":
    main()
