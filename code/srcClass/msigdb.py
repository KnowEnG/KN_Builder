"""Extension of utilities.py to provide functions required to check the
version information of msigdb and determine if it needs to be updated.

Classes:
    Msigdb: Extends the SrcClass class and provides the static variables and
        msigdb specific functions required to perform a check on msigdb.

Functions:
    get_SrcClass: returns a Msigdb object
    main: runs compare_versions (see utilities.py) on a Msigdb object
"""
import urllib.request
import re
import time
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
    return Msigdb(args)

class Msigdb(SrcClass):
    """Extends SrcClass to provide msigdb specific check functions.

    This Msigdb class provides source-specific functions that check the
    msigdb version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Msigdb with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'msigdb'
        url_base = 'http://www.broadinstitute.org/gsea/'
        aliases = {"c2.cgp": "curated_genes_cpg",
                   "c3.mir": "motif_gene_mir",
                   "c4.cgn": "comp_genes_cgn",
                   "c4.cm": "onco_sigs_cm",
                   "c6.all": "oncogenic_signatures_all",
                   "c7.all": "immunologic_signatures_all"}
        super(Msigdb, self).__init__(name, url_base, aliases, args)
        self.date_modified = 'unknown'

        self.source_url = "http://software.broadinstitute.org/gsea/msigdb/"
        self.image = "http://software.broadinstitute.org/gsea/images/MSigDB-logo1.gif"
        self.reference = ("Subramanian A, Tamayo P, Mootha VK, et al. Gene set enrichment "
                          "analysis: a knowledge-based approach for interpreting genome-wide "
                          "expression profiles. Proc Natl Acad Sci USA. 2005;102(43):15545-50.")
        self.pmid = 16199517
        self.license = ('MSigDB v6.0 is available under a Creative Commons style license, plus '
                        'additional terms for some gene sets. The full license terms are available '
                        '<a href="http://software.broadinstitute.org/gsea/msigdb_license_terms.jsp"'
                        '>here</a>.')

    def get_source_version(self, alias):
        """Return the release version of the remote msigdb:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Msigdb, self).get_source_version(alias)
        if version == 'unknown':
            url = self.url_base + 'msigdb/help.jsp'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                try:
                    d_line = line.decode()
                except UnicodeDecodeError:
                    continue
                match = re.search('MSigDB database v([^ ]*)', d_line)
                if match is not None:
                    response.close()
                    self.version[alias] = match.group(1)
                    break
            for alias_name in self.aliases:
                self.version[alias_name] = match.group(1)
            return self.version[alias]
        return version

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
            url = self.url_base + 'msigdb/help.jsp'
            response = urllib.request.urlopen(url)
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode('ascii', errors='ignore')
                match = re.search('updated ([^<]*)', d_line)
                if match is not None:
                    time_str = match.group(1)
                    response.close()
                    break
            time_format = "%B %Y"
            date_modified = time.mktime(time.strptime(time_str, time_format))
            self.date_modified = date_modified
        return self.date_modified

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
        url = self.url_base + 'resources/msigdb/' + version + '/'
        url += alias + '.v' + version + '.entrez.gmt'
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
        #e_meta_file = raw_line.replace('raw_line','edge_meta')

        #static column values
        alias = version_dict['alias']
        source = version_dict['source']
        n1type = 'property'
        n_type = 'Property'
        n1spec = '0'
        n1hint = source + '_' + alias
        n2type = 'gene'
        n2spec = '9606'  # assumption of human genes is occasionally incorrect
        n2hint = 'EntrezGene'
        et_hint = source + '_' + alias.replace(".", "_")
        score = 1

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]
                n1_orig_name = raw[0]
                n1_url = raw[1]
                hasher = hashlib.md5()
                hasher.update(n1_orig_name.encode())
                n1_chksum = hasher.hexdigest()
                n1_kn_id = cf.pretty_name('msig_' + n1_chksum)
                n1_kn_name = cf.pretty_name('msig_' + n1_orig_name)
                n1hint = n1_kn_name
                n_meta_writer.writerow([n1_kn_id, 'orig_desc', n1_orig_name])
                n_meta_writer.writerow([n1_kn_id, 'link', n1_url])
                n_writer.writerow([n1_kn_id, n1_kn_name, n_type])
                for n2_id in raw[2:]:
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1_kn_id, n1hint, n1type, n1spec,\
                        n2_id, n2hint, n2type, n2spec, et_hint,\
                        str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1_kn_id, n1hint, n1type, n1spec, \
                            n2_id, n2hint, n2type, n2spec, et_hint, score, \
                            t_chksum])
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)

def main():
    """Runs compare_versions (see utilities.compare_versions) on a Msigdb
    object

    This runs the compare_versions function on a Msigdb object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Msigdb.
    """
    compare_versions(Msigdb())

if __name__ == "__main__":
    main()
