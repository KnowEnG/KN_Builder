"""Extension of utilities.py to provide functions required to check the
version information of go and determine if it needs to be updated.

Classes:
    Go: extends the SrcClass class and provides the static variables and
        go specific functions required to perform a check on go.

Functions:
    get_SrcClass: returns a Go object
    main: runs compare_versions (see utilities.py) on a Go object
"""
import urllib.request
import re
import time
import os
import json
import csv
import hashlib
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
    return Go(args)

class Go(SrcClass):
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
        name = 'go'
        url_base = 'http://geneontology.org/gene-associations/'
        aliases = dict()
        super(Go, self).__init__(name, url_base, aliases, args)
        self.aliases = self.get_aliases(args)
        self.chunk_size = 250000

        self.source_url = "http://www.geneontology.org/"
        self.image = "https://avatars3.githubusercontent.com/u/7750835?v=3&s=200"
        self.reference = ("Gene Ontology Consortium: going forward. Nucleic Acids Res. "
                          "2015;43(Database issue):D1049-56.")
        self.pmid = 25428369
        self.license = 'Creative commons license attribution 4.0 international'

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
        alias_dict = {"obo_map": "ontology"}
        go_url = self.url_base + 'go_annotation_metadata.all.json'
        go_resp = urllib.request.urlopen(go_url).readall().decode()
        go_resources = json.loads(go_resp)
        go_dict = dict()
        for resource in go_resources['resources']:
            label = resource['label']
            if ' ' not in label or 'Reference' in label:
                continue
            if label == 'Canis lupus familiaris':
                label = 'Canis familiaris'
            go_dict[label] = resource['id']
        for species in sp_dict:
            species = species.capitalize().replace('_', ' ')
            if species in go_dict:
                alias_dict[go_dict[species]] = species
        return alias_dict

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the date modified of the remote file for the given alias.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        if alias == 'obo_map':
            return float(0)
        url_download_page = ('http://geneontology.org/gene-associations/'
                             'go_annotation_metadata.all.js')
        response = urllib.request.urlopen(url_download_page)
        cur_id = ''
        ret_str = float(0)
        t_format = "%m/%d/%Y"
        for line in response:
            d_line = line.decode()
            alias_match = re.search(r'"id": "(\S+)",', d_line)
            if alias_match is not None:
                if alias_match.group(1) == alias:
                    cur_id = alias
                else:
                    cur_id = ''
            date_match = re.search(r'"submissionDate": "(\S+)"', d_line)
            if (date_match is not None) and (cur_id == alias):
                t_str = date_match.group(1)
                ret_str = time.mktime(time.strptime(t_str, t_format))
                break
        response.close()
        return ret_str

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
        if alias == 'obo_map':
            return 'http://purl.obolibrary.org/obo/go.obo'
        go_url = self.url_base + 'go_annotation_metadata.all.json'
        go_resp = urllib.request.urlopen(go_url).readall().decode()
        go_resources = json.loads(go_resp)
        for resource in go_resources['resources']:
            if resource['id'] == alias:
                return self.url_base + resource['gaf_filename']

    def create_mapping_dict(self, filename, key_col=3, value_col=4):
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
        term_map = dict()
        n_type = 'Property'
        n_meta_file = filename.replace('raw_line', 'node_meta')
        node_file = filename.replace('raw_line', 'node')
        orig_id, kn_id, orig_name, kn_name = ['', '', '', '']
        skip = True
        with open(filename) as infile, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            reader = csv.reader(infile, delimiter='\t')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in reader:
                raw = line[3]
                if raw.startswith('[Term]'):
                    skip = False
                    orig_id, kn_id, orig_name, kn_name = ['', '', '', '']
                    continue
                if raw.startswith('[Typedef]'):
                    skip = True
                    continue
                if skip:
                    continue
                if raw.startswith('id: '):
                    orig_id = raw[4:].strip()
                    kn_id = cf.pretty_name(orig_id)
                    continue
                if raw.startswith('name: '):
                    orig_name = raw[6:].strip()
                    kn_name = cf.pretty_name('go_' + orig_name)
                    term_map[orig_id] = kn_id + '::' + kn_name
                    n_writer.writerow([kn_id, kn_name, n_type])
                    n_meta_writer.writerow([kn_id, 'orig_desc', orig_name])
                    n_meta_writer.writerow([kn_id, 'orig_id', orig_id])
                if raw.startswith('alt_id: '):
                    alt_id = raw[8:].strip()
                    term_map[alt_id] = kn_id + '::' + kn_name
                    n_meta_writer.writerow([kn_id, 'alt_alias', alt_id])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)

        return term_map

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
        e_meta_file = raw_line.replace('raw_line', 'edge_meta')

        #static column values
        alias = version_dict['alias']
        source = version_dict['source']
        n1type = 'property'
        n1spec = '0'
        n2type = 'gene'

        info_type1 = 'reference'
        info_type2 = 'evidence'

        #mapping files
        obo_file = os.path.join('..', 'obo_map', 'go.obo_map.json')
        with open(obo_file) as infile:
            obo_map = json.load(infile)

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(e_meta_file, 'w') as e_meta:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            e_meta_writer = csv.writer(e_meta, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]

                # skip commented lines
                comment_match = re.match('!', raw[0])
                if comment_match is not None:
                    continue

                qualifier = raw[3]
                # skip "NOT" annotations
                not_match = re.search('NOT', qualifier)
                if not_match is not None:
                    continue

                n1orig = raw[4]
                n1_mapped = obo_map.get(n1orig, "unmapped:no-name::unmapped")
                (n1_id, n1hint) = n1_mapped.split('::')

                n2spec_str = raw[12].split("|", 1)[0].rstrip() #only take first species
                n2spec = n2spec_str.split(":", 1)[1] #remove label taxon:
                if n2spec == '559292': #manually overwrite taxid for Scer
                    n2spec = '4932'

                reference = raw[5]
                anno_evidence = raw[6]

                score = 2
                et_hint = 'gene_ontology'
                if anno_evidence == 'IEA':
                    score = 1

                n2_id = raw[1]
                n2hint = raw[0]

                if n2hint == "UniProtKB":
                    n2hint = "uniprot_gn"
                if n1hint == "UniProtKB":
                    n1hint = "uniprot_gn"

                for idx in range(1, 3):  # loop twice
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1_id, n1hint, n1type, n1spec,\
                    n2_id, n2hint, n2type, n2spec, et_hint, str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1_id, n1hint, n1type, n1spec, \
                        n2_id, n2hint, n2type, n2spec, et_hint, score, t_chksum])
                    n2_id = raw[2]

                e_meta_writer.writerow([chksm, info_type1, reference])
                e_meta_writer.writerow([chksm, info_type2, anno_evidence])
            outfile = e_meta_file.replace('edge_meta', 'unique.edge_meta')
            tu.csu(e_meta_file, outfile)

def main():
    """Runs compare_versions (see utilities.compare_versions) on a Go object.

    This runs the compare_versions function on a Go object to find the version
    information of the source and determine if a fetch is needed. The version
    information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Go.
    """
    compare_versions(Go())

if __name__ == "__main__":
    main()
