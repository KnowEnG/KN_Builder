"""Extension of utilities.py to provide functions required to check the
version information of msigdb and determine if it needs to be updated.

Classes:
    Msigdb: Extends the SrcClass class and provides the static variables and
        msigdb specific functions required to perform a check on msigdb.

Functions:
    get_SrcClass: returns a Msigdb object
    main: runs compare_versions (see utilities.py) on a Msigdb object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import time
import csv

def get_SrcClass():
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.
    
    Args:
    
    Returns:
        class: a source class object
    """
    return Msigdb()

class Msigdb(SrcClass):
    """Extends SrcClass to provide msigdb specific check functions.

    This Msigdb class provides source-specific functions that check the
    msigdb version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self):
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
        super(Msigdb, self).__init__(name, url_base, aliases)
        self.date_modified = 'unknown'

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
                except:
                    continue
                match = re.search('MSigDB database v([^ ]*)', d_line)
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
        return super(Msigdb, self).get_local_file_info(alias)

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
        return super(Msigdb, self).get_remote_file_size(url)

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
        return super(Msigdb, self).is_map(alias)

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
        return super(Msigdb, self).get_dependencies(alias)

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
        return super(Msigdb, self).create_mapping_dict(filename)

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
        table_file = '.'.join(rawline.split('.')[:-2]) + '.edge.txt'
        #e_meta_file = '.'.join(rawline.split('.')[:-2]) + '.edge_meta.txt'
        n_meta_file = '.'.join(rawline.split('.')[:-2]) + '.node_meta.txt'

        #static column values
        alias = version_dict['alias']
        source = version_dict['source']
        n1type = 'property'
        n1spec = '0'
        n1hint = source + '_' + alias
        n2type = 'gene'
        n2spec = 9606  # assumption of human genes is occasionally incorrect
        n2hint = 'EntrezGene'
        et_hint = source + '_' + alias
        score = 1

        info_type1 = 'synonym'
        info_type2 = 'link'
        node_num = 1

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(n_meta_file, 'w') as n_meta:
            reader = csv.reader(infile, delimiter='\t')
            edge_writer = csv.writer(edges, delimiter='\t')
            n_meta_writer = csv.writer(n_meta, delimiter='\t')
            for line in reader:
                chksm = line[2]
                raw = line[3:]
                n1_orig_name = raw[0]
                n1_url = raw[1]
                n1 = 'msigdb_' + re.sub('[^a-zA-Z0-9]','_',n1_orig_name)[0:35]
                n_meta_writer.writerow([chksm, node_num, info_type1, n1_orig_name])
                n_meta_writer.writerow([chksm, node_num, info_type2, n1_url])
                for n2 in raw[2:]:
                    edge_writer.writerow([chksm, n1, n1hint, n1type, n1spec, \
                        n2, n2hint, n2type, n2spec, et_hint, score])
                
if __name__ == "__main__":
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
