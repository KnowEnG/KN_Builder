"""Extension of utilities.py to provide functions required to check the
version information of pathcom and determine if it needs to be updated.

Classes:
    Pathcom: Extends the SrcClass class and provides the static variables and
        pathcom specific functions required to perform a check on pathcom.

Functions:
    get_SrcClass: returns a Pathcom object
    main: runs compare_versions (see utilities.py) on a Pathcom object
"""
import urllib.request
import re
import hashlib
import csv
import table_utilities as tu
from check_utilities import SrcClass, compare_versions
import config_utilities as cf

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Pathcom(args)

class Pathcom(SrcClass):
    """Extends SrcClass to provide pathcom specific check functions.

    This Pathcom class provides source-specific functions that check the
    pathcom version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Pathcom with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'pathcom'
        url_base = 'http://www.pathwaycommons.org/archives/PC2/'
        aliases = {"all":""}
        super(Pathcom, self).__init__(name, url_base, aliases, args)

        self.source_url = "http://www.pathwaycommons.org/"
        self.image = "https://pbs.twimg.com/profile_images/862675480281042944/PblJi9Va.jpg"
        self.reference = ("Cerami EG, Gross BE, Demir E, et al. Pathway Commons, a web resource "
                          "for biological pathway data. Nucleic Acids Res. "
                          "2011;39(Database issue):D685-90.")
        self.pmid = 21071392
        self.license = ('Full list of data sources are available <a '
                        'href="http://www.pathwaycommons.org/pc2/datasources">here</a>.')

    def get_source_version(self, alias):
        """Return the release version of the remote pathcom:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Pathcom, self).get_source_version(alias)
        if version == 'unknown':
            response = urllib.request.urlopen('http://www.pathwaycommons.org/pc2/downloads')
            the_page = response.readlines()
            for line in the_page:
                d_line = line.decode()
                match = re.search('Pathway Commons .* version ([^ ,]*)', d_line)
                if match is not None:
                    response.close()
                    self.version[alias] = match.group(1)
                    break
            for alias_name in self.aliases:
                self.version[alias_name] = match.group(1)
            return self.version[alias]
        return version

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
        url = self.url_base
        url += 'v{0}/PathwayCommons{0}.All.hgnc.txt.gz'
        url = url.format(self.get_source_version(alias))
        print(url)
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
        e_meta_file = raw_line.replace('raw_line', 'edge_meta')

        #static column values
        n1type = 'gene' #ignoring chemicals
        n1hint = 'UNIPROT_GN'
        n1spec = 'unknown'
        n2type = n1type #ignoring chemicals
        n2hint = n1hint
        n2spec = n1spec
        n3_type = 'property'
        n3hint = 'unknown'
        n3spec = 'unknown'
        score = '1'
        n_type = 'Property'

        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(e_meta_file, 'w') as e_meta, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            e_meta_writer = csv.writer(e_meta, delimiter='\t', lineterminator='\n')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                if line[1] == '1': #skip header
                    continue
                chksm = line[0]
                raw = line[3:]
                if len(raw) != 7: #extended information
                    continue
                (n1id, et_hint, n2id, src, publist, n3id, mediator_ids) = raw
                et_hint = 'pathcom_' + et_hint.replace('-', '_')
                #n1-n2 edge
                hasher = hashlib.md5()
                hasher.update('\t'.join([chksm, n1id, n1hint, n1type, n1spec,
                                         n2id, n2hint, n2type, n2spec, et_hint,
                                         score]).encode())
                t_chksum = hasher.hexdigest()
                edge_writer.writerow([chksm, n1id, n1hint, n1type, n1spec,
                                      n2id, n2hint, n2type, n2spec, et_hint,
                                      score, t_chksum])
                e_meta_writer.writerow([chksm, 'original_source', src])
                if publist:
                    e_meta_writer.writerow([chksm, 'reference', publist])
                #pathway edge
                if n3id:
                    kn_n3id = cf.pretty_name('paco_' + n3id)
                    n_writer.writerow([kn_n3id, kn_n3id, n_type])
                    n_meta_writer.writerow([kn_n3id, 'orig_id', n3id])
                    for node in [n1id, n2id]:
                        hasher = hashlib.md5()
                        hasher.update('\t'.join([chksm, kn_n3id, n3hint, n3_type,
                                                 n3spec, node, n1hint, n1type, n1spec,
                                                 'pathcom_pathway', score]).encode())
                        t_chksum = hasher.hexdigest()
                        edge_writer.writerow([chksm, kn_n3id, n3hint, n3_type,
                                              n3spec, node, n1hint, n1type, n1spec,
                                              'pathcom_pathway', score, t_chksum])
        outfile = e_meta_file.replace('edge_meta', 'unique.edge_meta')
        tu.csu(e_meta_file, outfile, [1, 2, 3])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)


def main():
    """Runs compare_versions (see utilities.compare_versions) on a Pathcom
    object

    This runs the compare_versions function on a Pathcom object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Pathcom.
    """
    compare_versions(Pathcom())

if __name__ == "__main__":
    main()
