"""Extension of utilities.py to provide functions required to check the
version information of lincs and determine if it needs to be updated.

Classes:
    Lincs: Extends the SrcClass class and provides the static variables and
        lincs specific functions required to perform a check on lincs.

Functions:
    get_SrcClass: returns a Lincs object
    main: runs compare_versions (see utilities.py) on a Lincs object
"""
from check_utilities import SrcClass, compare_versions
import urllib.request
import re
import hashlib
import csv
import os
import time
import config_utilities as cf
import subprocess
import shutil
import json

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Lincs(args)

class Lincs(SrcClass):
    """Extends SrcClass to provide lincs specific check functions.

    This Lincs class provides source-specific functions that check the
    lincs version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Lincs with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'lincs'
        url_base = 's3://data.lincscloud.org/l1000/'
        aliases = { "level4": "level4/",
                    "exp_meta": "metadata/",
                    "gene_info": ("http://eh3.uc.edu/genomics/lincs/dcic/"
                                    "public/geneInfo/geneInfo.tab"),
                    "baseline_gene_expression": ("http://eh3.uc.edu/genomics/"
                                    "lincs/dcic/public/baselineGeneExpression/"
                                    "baselineGeneExpression.tab")
                    }
        super(Lincs, self).__init__(name, url_base, aliases, args)

    def get_source_version(self, alias):
        """Return the release version of the remote lincs:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias. This value is
        stored in the self.version dictionary object.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        version = super(Lincs, self).get_source_version(alias)
        if version == 'unknown':
            output = subprocess.Popen(['s3cmd', 'ls', self.url_base +
                'level4/'], stdout=subprocess.PIPE).stdout.readlines()
            file = output[-1].decode()
            (date, mtime, size, path) = file.split()
            match = re.search('zspc_n(\d*x\d*).gctx', path)
            if match is not None:
                self.version[alias] = match.group(1)
            else:
                self.version[alias] = "unknown"
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
        return super(Lincs, self).get_local_file_info(alias)

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
        if alias in ['level4', 'exp_meta']:
            output = subprocess.Popen(['s3cmd', 'ls', url],
                stdout=subprocess.PIPE).stdout
            file = output.readlines()[-1].decode()
            (date, mtime, size, path) = file.split()
            return int(size)
        else:
            return super(Lincs, self).get_remote_file_size(url)

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
        if alias in ['level4', 'exp_meta']:
            output = subprocess.Popen(['s3cmd', 'ls', url],
                stdout=subprocess.PIPE).stdout
            file = output.readlines()[-1].decode()
            (date, mtime, size, path) = file.split()
            time_str = date + ' ' + mtime
            time_format = "%Y-%m-%d %H:%M"
            return time.mktime(time.strptime(time_str, time_format))
        else:
            return super(Lincs, self).get_remote_file_modified(url)

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
        if alias in ['level4', 'exp_meta']:
            url = self.url_base + self.aliases[alias]
            output = subprocess.Popen(['s3cmd', 'ls', url],
                stdout=subprocess.PIPE).stdout
            file = output.readlines()[-1].decode()
            (date, mtime, size, path) = file.split()
            return path
        else:
            return self.aliases[alias]

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
        if alias == 'level4':
            return False
        else:
            return True

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
        if alias is not 'level4':
            return list()
        return super(Lincs, self).get_dependencies(alias)

    def create_mapping_dict(self, filename, args):
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
        gctx_file = filename
        print(os.getcwd())
        tab_file = os.path.join('..', 'baseline_gene_expression',
                '.'.join(['lincs', 'baseline_gene_expression', 'txt']))
        cmd = ['python',
               os.path.join(args.local_dir, args.code_path, args.src_path,
               'affy2ens_utilities.py'), gctx_file, tab_file, args.redis_host,
               args.redis_port]
        print(' '.join(cmd))
        subprocess.Popen(cmd).communicate()
        with open(os.path.splitext(tab_file)[0] + '.json') as infile:
            return json.load(infile)

    def table(self, rawline, version_dict):
        """Uses the provided rawline file to produce an edge file.

        This returns noting but produces the edge file formatted files from the
        provided rawline file (performs both the conv and table steps).
        It outputs an edge_mapped file in the format (n1, n2, line_checksum,
        edge_type, weight, status, status_desc), where status is production if
        both nodes mapped and unmapped otherwise.

        Args:
            rawline(str): The path to the rawline file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.

        Returns:
        """

        #outfiles
        table_file = rawline.replace('rawline','conv')

        #static column values
        et_map = 'LINCS_signature'

        #open mapping files
        map_file = os.path.join('..', 'baseline_gene_expression',
                            'lincs.baseline_gene_expression.json')
        print(map_file)
        print(os.getcwd())
        head_file = os.path.join(os.path.dirname(map_file), 'headers.json')
        with open(map_file) as infile:
            lincs_map = json.load(infile)
        with open(head_file) as infile:
            headers = json.load(infile)

        with open(rawline, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges:
            writer = csv.writer(edges, delimiter='\t')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                n1_map = line[3]
                if n1_map == '':
                    continue
                scores = line[4:]
                evaluated = [0]*len(scores)
                for i in range(0, len(scores)):
                    weight = scores[i]
                    if abs(float(weight)) < 2.5 or evaluated[i]:
                        continue
                    evaluated[i] = 1
                    n2 = headers[str(i)]
                    (n2_map, probe_list, idx_list) = lincs_map[n2]
                    if 'unmapped' in n1_map or n1_map == 'NA':
                        continue
                    for idx in idx_list:
                        if abs(float(scores[idx])) > abs(float(weight)):
                            weight = scores[idx]
                        evaluated[idx] = 1
                    if float(weight) < 0:
                        et_map = 'LINCS_down_signature'
                        weight = str(abs(float(weight)))
                    else:
                        et_map = 'LINCS_up_signature'
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([n1_map, n2_map, et_map]).encode())
                    e_chksum = hasher.hexdigest()
                    writer.writerow([n1_map, n2_map, et_map, weight, e_chksum])


def download(version_dict, args):
    """Returns the standardized path to the local file after downloading it
    from the source and unarchiving if needed.

    This returns the standardized path (path/source.alias.txt) for the
    source alias described in version_dict. If a download is needed
    (as determined by the check step), the remote file will be downloaded.

    Args:
        version_dict (dict): A dictionary describing the attributes of the
        alias for a source.

    Returns:
        str: The relative path to the newly downloaded file.
    """
    filename = version_dict['local_file_name']
    ret_file = '.'.join([version_dict['source'], version_dict['alias'], 'txt'])

    if not version_dict['fetch_needed'] and version_dict['local_file_exists']:
        #if version_dict['alias'] == 'level4':
        #    get_SrcClass(args).create_mapping_dict(filename, args)
        return os.path.relpath(ret_file)

    output = subprocess.Popen(['s3cmd', 'ls', version_dict['remote_url']],
        stdout=subprocess.PIPE).stdout
    file = output.readlines()[-1].decode()
    (date, mtime, size, path) = file.split()

    ###change --skip-existing --continue for nicer behavior
    ###this is a hack to prevent needing to download many times
    cmd = ['s3cmd', '--skip-existing', '--preserve', 'get', path, filename]
    print(' '.join(cmd))
    subprocess.Popen(cmd).communicate()
    if version_dict['alias'] == 'level4':
        #gctx_to_txt(filename, ret_file, args)
        get_SrcClass(args).create_mapping_dict(filename, args)
    else:
        shutil.copy2(filename, ret_file)
    return os.path.relpath(ret_file)


def gctx_to_txt(gctx_file, ret_file, args):
    cmd = ['python', os.path.join(args.local_dir, args.code_path, args.src_path,
            'gctx2tsv_utilities.py'), gctx_file, ret_file]
    print(' '.join(cmd))
    subprocess.Popen(cmd).communicate()
    return os.path.relpath(gctx_file.replace('gctx', 'txt'))

if __name__ == "__main__":
    """Runs compare_versions (see utilities.compare_versions) on a Lincs
    object

    This runs the compare_versions function on a Lincs object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Lincs.
    """
    compare_versions(Lincs())
