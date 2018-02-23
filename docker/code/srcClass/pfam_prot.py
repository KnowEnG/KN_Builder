"""Extension of utilities.py to provide functions required to check the
version information of pfam and determine if it needs to be updated.

Classes:
    PfamProt: extends the SrcClass class and provides the static variables and
        pfam specific functions required to perform a check on go.

Functions:
    get_SrcClass: returns a PfamProt object
    main: runs compare_versions (see utilities.py) on a PfamProt object
"""
import re
import os
import json
import csv
import hashlib
import math
import urllib.request
import urllib.error
import config_utilities as cf
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
    return PfamProt(args)

class PfamProt(SrcClass):
    """Extends SrcClass to provide go specific check functions.

    This Go class provides source-specific functions that check the go version
    information and determine if it differs from the current version in the
    Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Stringdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'pfam_prot'
        url_base = 'ftp://ftp.ebi.ac.uk/pub/databases/Pfam/'
        aliases = dict()
        super(PfamProt, self).__init__(name, url_base, aliases, args)
        self.aliases = self.get_aliases(args)

        self.sc_max = 100  # may want to load these
        self.sc_min = 2 # may want to load these

        self.source_url = "http://pfam.xfam.org/"
        self.image = "https://upload.wikimedia.org/wikipedia/commons/0/03/Pfam_logo.gif"
        self.reference = ("Finn RD, Coggill P, Eberhardt RY, et al. The Pfam protein families "
                          "database: towards a more sustainable future. Nucleic Acids Res. "
                          "2016;44(D1):D279-85.")
        self.pmid = 26673716
        self.license = 'Pfam is freely available under the Creative Commons Zero ("CC0") licence.'

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
            print(species, taxid, url, end=' ')
            try:
                urllib.request.urlopen(url)
            except urllib.error.URLError:
                print('err')
            else:
                alias_dict[taxid] = sp_abbrev
                print('ok')
        return alias_dict


    def get_source_version(self, alias):
        """Return the release version of the remote pfam:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be 'unknown' for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        if alias not in self.version:
            release_note_url = self.url_base + 'current_release/relnotes.txt'
            response = urllib.request.urlopen(release_note_url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search(r"RELEASE (\d+\.?\d*)", d_line)
                if match is not None:
                    response.close()
                    vers = match.group(1)
                    self.version[alias] = vers
                    return self.version[alias]
        return self.version[alias]

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. The url is constructed using the base_url and alias information.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        version = self.get_source_version(alias)
        url = self.url_base + 'releases/Pfam' + version + '/proteomes/' + alias + '.tsv.gz'
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
        n_meta_file = raw_line.replace('raw_line', 'node_meta')
        node_file = raw_line.replace('raw_line', 'node')
        #e_meta_file = raw_line.replace('raw_line', 'edge_meta')

        #static column values
        n1type = 'property'
        n_type = 'Property'
        n2type = 'gene'
        n1hint = 'Pfam/Family'
        n2hint = 'Uniprot_gn'
        et_hint = 'pfam_prot'
        n1spec = '0'
        map_dict = dict()
        src = 'pf'

        ###Map the file name
        species = (os.path.join('..', '..', 'id_map', 'species', 'species.json'))
        with open(species) as infile:
            species_map = json.load(infile)
        n2spec = version_dict['alias']

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split()
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]

                # skip commented lines
                comment_match = re.match('#', raw[0])
                if comment_match is not None:
                    continue

                orig_id = raw[5].strip()
                orig_name = raw[6].strip()
                kn_id = cf.pretty_name(src + '_' + orig_id)
                kn_name = cf.pretty_name(src + '_' + orig_name)
                map_dict[orig_id] = kn_id + '::' + kn_name
                n_writer.writerow([kn_id, kn_name, n_type])
                n_meta_writer.writerow([kn_id, 'orig_desc', orig_name])
                n_meta_writer.writerow([kn_id, 'orig_id', orig_id])
                n2orig = raw[0]
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
                    continue

                output = [chksm, kn_id, n1hint, n1type, n1spec,
                          n2orig, n2hint, n2type, n2spec, et_hint,
                          str(score)]
                hasher = hashlib.md5()
                hasher.update('\t'.join(output).encode())
                t_chksum = hasher.hexdigest()
                edge_writer.writerow(output + [t_chksum])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)


def main():
    """Runs compare_versions (see utilities.compare_versions) on a PfamProt object.

    This runs the compare_versions function on a PfamProt object to find the version
    information of the source and determine if a fetch is needed. The version
    information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in PfamProt.
    """
    compare_versions(PfamProt())

if __name__ == "__main__":
    main()
