"""module for checking if source needs to be updated in Knowledge Network (KN).

Contains the class SrcClass which serves as the base class for each supported
source in the KN.

Contains module functions::

    get_SrcClass(args)
    compare_versions(SrcClass)
    check(module, args=None)
    main_parse_args()

Examples:
    To run check on a single source (e.g. dip)::

        $ python3 code/check_utilities.py dip

    To view all optional arguments that can be specified::

        $ python3 code/check_utilities.py -h

"""

import urllib.request
import urllib.error
import os
import time
import json
import csv
import sys
from argparse import ArgumentParser
import config_utilities as cf
import table_utilities as tu
import mysql_utilities as mu
import import_utilities as iu

class SrcClass(object):
    """Base class to be extended by each supported source in KnowEnG.

    This SrcClass provides default functions that should be extended
    or overridden by any source which is added to the Knowledge Network (KN).

    Attributes:
        name (str): The name of the remote source to be included in the KN.
        url_base (str): The base url of the remote source, which may need
            additional processing to provide an actual download link (see
            get_remote_url).
        aliases (dict): A dictionary with subsets of the source which will be
            included in the KN  as the keys (e.g. different species, data
            types, or interaction types), and a short string with information
            about the alias as the value.
        remote_file (str): The name of the file to extract if the remote source
            is a directory
        version (dict): The release version of each alias in the source.
    """

    def __init__(self, src_name, base_url, aliases, args=None):
        """Init a SrcClass object with the provided parameters.

        Constructs a SrcClass object with the provided parameters, which should
        be provided by any class extending SrcClass.

        Args:
            src_name (str): The name of the remote source to be included in
                the KN. Must be provided by the extending class.
            url_base (str): The base url of the remote source, which may need
                additional processing to provide an actual download link (see
                get_remote_url). Must be provided by the extending class.
            aliases (dict): A dictionary with subsets of the source which will
                be included in the KN  as the keys (e.g. different species,
                data types, or interaction types), and a short string with
                information about the alias as the value.
            args (Namespace): args as populated namespace or 'None' for defaults
        """
        if args is None:
            args = cf.config_args()
        self.name = src_name
        self.url_base = base_url
        self.aliases = aliases
        self.remote_file = ''
        self.version = dict()
        self.args = args
        self.chunk_size = 500000

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
        return dict()

    def get_source_version(self, alias):
        """Return the release version of the remote source:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias unless the
        the alias can have a different release version than the source
        (this will be source dependent). This value is stored in the
        self.version dictionary object. If the value does not already exist,
        all aliases versions are initialized to 'unknown'.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The remote version of the source.
        """
        if alias not in self.version:
            for alias_name in self.aliases:
                self.version[alias_name] = 'unknown'
        return self.version[alias]

    def get_local_file_info(self, alias):
        """Return a dictionary with the local file information for the alias.

        This returns the local file information for a given source alias, which
        will always contain the following keys::

            'local_file_name' (str):        name of the file locally
            'local_file_exists' (bool):     boolean if file exists at path
                                            indicated by 'local_file_name'

        and will also contain the following if 'local_file_exists' is True::

            'local_size' (int):     size of local file in bytes
            'local_date' (float):   time of last modification time of local
                                    file in seconds since the epoch

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        f_dir = os.path.join(self.args.working_dir, self.args.data_path, self.name)
        f_dir = os.path.join(f_dir, alias)
        url = self.get_remote_url(alias)
        filename = os.path.basename(url).replace('%20', '_')
        file = os.path.join(f_dir, filename)
        local_dict = dict()
        local_dict['local_file_name'] = filename
        local_dict['local_file_exists'] = os.path.isfile(file)
        if not local_dict['local_file_exists']:
            return local_dict
        local_dict['local_size'] = os.path.getsize(file)
        local_dict['local_date'] = os.path.getmtime(file)
        return local_dict

    def get_local_version_info(self, alias, args):
        """Return a dictionary with the local information for the alias.

        This returns the local information for a given source alias, as
        retrieved from the msyql database and formated as a dicitonary object.
        (see mysql_utilities.get_file_meta). It adds the local_file_name and
        local_file_exists to the fields retrieved from the database, which
        are the name of the file locally and a boolean indicating if it already
        exists on disk, respectively.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """
        file_id = '.'.join([self.name, alias])
        file_meta = mu.get_file_meta(file_id, args)
        f_dir = os.path.join(self.args.working_dir, self.args.data_path, self.name)
        f_dir = os.path.join(f_dir, alias)
        url = self.get_remote_url(alias)
        filename = os.path.basename(url).replace('%20', '_')
        file = os.path.join(f_dir, filename)
        file_meta['local_file_name'] = filename
        file_meta['local_file_exists'] = os.path.isfile(file)
        return file_meta


    def get_remote_file_size(self, alias):
        """Return the remote file size.

        This returns the remote file size as specificied by the
        'content-length' page header. If the remote file size is unknown, this
        value should be -1.

        Args:
            remote_url (str): The url of the remote file to get the size of.

        Returns:
            int: The remote file size in bytes.
        """
        remote_url = self.get_remote_url(alias)
        try:
            response = urllib.request.urlopen(remote_url)
            print(response.headers)
            return int(response.headers['content-length'])
        except (TypeError, ValueError, urllib.error.URLError):
            return -1

    def get_remote_file_modified(self, alias):
        """Return the remote file date modified.

        This returns the remote file date modifed as specificied by the
        'last-modified' page header.

        Args:
            remote_url (str): The url of the remote file to get the date
                modified of.

        Returns:
            float: time of last modification time of remote file in seconds
                since the epoch
        """
        remote_url = self.get_remote_url(alias)
        try:
            response = urllib.request.urlopen(remote_url)
            time_str = response.headers['last-modified']
            time_format = "%a, %d %b %Y %H:%M:%S %Z"
            return time.mktime(time.strptime(time_str, time_format))
        except (urllib.error.URLError, ValueError, TypeError, ConnectionResetError):
            return float(0)

    def get_remote_url(self, alias):
        """Return the remote url needed to fetch the file corresponding to the
        alias.

        This returns the url needed to fetch the file corresponding to the
        alias. By default this returns self.base_url.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            str: The url needed to fetch the file corresponding to the alias.
        """
        return self.url_base

    def is_map(self, alias):
        """Return a boolean representing if the provided alias is used for
        source specific mapping of nodes or edges.

        This returns a boolean representing if the alias corresponds to a file
        used for mapping. By default this returns True if the alias ends in
        '_map' and False otherwise.

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            bool: Whether or not the alias is used for mapping.
        """
        return alias[-4:] == '_map'

    def get_dependencies(self, alias):
        """Return a list of other aliases that the provided alias depends on.

        This returns a list of other aliases that must be processed before
        full processing of the provided alias can be completed. By default,
        returns a list of all aliases which are considered mapping files (see
        is_map)

        Args:
            alias(str): An alias defined in self.aliases.

        Returns:
            list: The other aliases defined in self.aliases that the provided
                alias depends on.
        """
        depends = list()
        if self.is_map(alias):
            return depends
        for alias_name in self.aliases:
            if alias_name == alias:
                continue
            elif self.is_map(alias_name):
                depends.append(alias_name)
        return depends

    def create_mapping_dict(self, filename, key_col=3, value_col=4):
        """Return a mapping dictionary for the provided file.

        This returns a dictionary for use in mapping nodes or edge types from
        the file specified by filetype. By default it opens the file specified
        by filename creates a dictionary using the key_col column as the key
        and the value_col column as the value.

        Args:
            filename (str): The name of the file containing the information
                needed to produce the maping dictionary.
            key_col (int): The column containing the key for creating the
                dictionary. By default this is column 3.
            value_col (int): The column containing the value for creating the
                dictionary. By default this is column 4.

        Returns:
            dict: A dictionary for use in mapping nodes or edge types.
        """
        src = filename.split('.')[0]
        alias = filename.split('.')[1]
        map_dict = dict()
        n_meta_file = filename.replace('raw_line', 'node_meta')
        node_file = filename.replace('raw_line', 'node')
        if not self.is_map(alias):
            return map_dict
        with open(filename, 'rb') as map_file, \
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            reader = csv.reader((line.decode('utf-8') for line in map_file),
                                delimiter='\t')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in reader:
                chksm = line[2]
                orig_id = line[key_col].strip()
                orig_name = line[value_col].strip()
                kn_id = cf.pretty_name(orig_id)
                kn_name = cf.pretty_name(src + '_' + orig_name)
                map_dict[orig_id] = kn_id + '::' + kn_name
                n_writer.writerow([kn_id, kn_name])
                n_meta_writer.writerow([kn_id, 'orig_desc', orig_name])
                n_meta_writer.writerow([kn_id, 'orig_id', orig_id])
        outfile = node_file.replace('node', 'unique.node')
        tu.csu(node_file, outfile)
        outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
        tu.csu(n_meta_file, outfile)
        return map_dict

    def table(self, raw_line, version_dict):
        """Uses the provided raw_lines file to produce a 2table_edge file, an
        edge_meta file, and a node_meta file (only for property nodes).

        This returns nothing but produces the 2table formatted files from the
        provided raw_lines file::

            raw_lines table (file, line num, line_chksum, raw_line)
            2tbl_edge table (line_cksum, n1name, n1hint, n1type, n1spec,
                            n2name, n2hint, n2type, n2spec, et_hint, score)
            edge_meta (line_cksum, info_type, info_desc)
            node_meta (node_id,
                       info_type (alt_alias, relationship, experiment, or link),
                       info_desc (text))

        By default this function does nothing (must be overridden)

        Args:
            raw_line (str): The path to the raw_lines file
            version_dict (dict): A dictionary describing the attributes of the
                alias for a source.
        """
        return

def get_SrcClass(args, *posargs, **kwargs):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:
        args (Namespace): args as populated namespace or 'None' for defaults

    Returns:
        SrcClass: a source class object
    """
    return SrcClass(args, *posargs, **kwargs)

def compare_versions(src_obj, args=None):
    """Return a dictionary with the version information for each alias in the
    source and write a dictionary for each alias to file.

    This returns a nested dictionary describing the version information of each
    alias in the source. The version information is also printed.

    Args:
        src_obj (SrcClass): A SrcClass object for which the comparison should
            be performed.
        args (Namespace): args as populated namespace or 'None' for defaults


    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in src_obj.  For each alias the following keys are
            defined::

                'source' (str):                 The source name,
                'alias' (str):                  The alias name,
                'alias_info' (str):             A short string with information
                                                about the alias,
                'is_map' (bool):                See is_map,
                'dependencies' (lists):         See get_dependencies,
                'remote_url' (str):             See get_remote_url,
                'remote_date' (float):          See get_remote_file_modified,
                'remote_version' (str):         See get_source_version,
                'remote_file' (str):            File to extract if remote file
                                                location is a directory,
                'remote_size' (int):            See get_remote_file_size,
                'local_file_name' (str):        See get_local_version_info,
                'file_exists' (bool):           See get_local_version_info,
                'fetch_needed' (bool):          True if file needs to be downloaded
                                                from remote source. A fetch will
                                                be needed if the local file does
                                                not exist, or if the local and
                                                remote files have different date
                                                modified or file sizes.

    """
    version_dict = dict()
    file_meta = dict()
    for alias in src_obj.aliases:
        print('Comparing versions for {0}'.format(alias))
        file_meta[alias] = src_obj.get_local_version_info(alias, args)
        version_dict[alias] = dict()
        version_dict[alias]['source'] = src_obj.name
        version_dict[alias]['alias'] = alias
        version_dict[alias]['alias_info'] = src_obj.aliases[alias]
        version_dict[alias]['is_map'] = src_obj.is_map(alias)
        version_dict[alias]['dependencies'] = src_obj.get_dependencies(alias)
        remote_url = src_obj.get_remote_url(alias)
        version_dict[alias]['remote_url'] = remote_url
        version_dict[alias]['remote_file'] = src_obj.remote_file
        version_dict[alias]['remote_date'] = \
            src_obj.get_remote_file_modified(alias)
        version_dict[alias]['remote_version'] = \
            src_obj.get_source_version(alias)
        version_dict[alias]['remote_size'] = src_obj.get_remote_file_size(alias)
        version_dict[alias]['local_file_name'] = \
            file_meta[alias]['local_file_name']
        version_dict[alias]['file_exists'] = \
            file_meta[alias]['file_exists']
        version_dict[alias]['source_url'] = src_obj.source_url
        version_dict[alias]['image'] = src_obj.image
        version_dict[alias]['reference'] = src_obj.reference
        version_dict[alias]['pmid'] = src_obj.pmid
        version_dict[alias]['license'] = src_obj.license


        if not file_meta[alias]['file_exists']:
            version_dict[alias]['fetch_needed'] = True
            continue

        l_size = file_meta[alias]['size']
        r_size = version_dict[alias]['remote_size']
        l_date = file_meta[alias]['date']
        r_date = version_dict[alias]['remote_date']
        l_version = file_meta[alias]['version']
        r_version = version_dict[alias]['remote_version']

        if r_size == -1 and r_date == 0 and r_version == 'unknown':
            version_dict[alias]['fetch_needed'] = True
        elif l_size == r_size and l_date == r_date and l_version == r_version:
            version_dict[alias]['fetch_needed'] = False
        else:
            version_dict[alias]['fetch_needed'] = True

    f_dir = os.path.join(src_obj.args.working_dir, src_obj.args.data_path,
                         src_obj.name)
    os.makedirs(f_dir, exist_ok=True)
    for alias in src_obj.aliases:
        a_dir = os.path.join(f_dir, alias)
        os.makedirs(a_dir, exist_ok=True)
        f_name = os.path.join(a_dir, 'file_metadata.json')
        with open(f_name, 'w') as outfile:
            json.dump(version_dict[alias], outfile, indent=4, sort_keys=True)
    #print(json.dumps(version_dict, indent=4, sort_keys=True))
    print("printing file_metadata.json")
    return version_dict

def check(module, args=None):
    """Runs compare_versions(SrcClass) on a 'module' object

    This runs the compare_versions function on a 'module' object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Args:
        module (str): string name of module defining source specific class
        args (Namespace): args as populated namespace or 'None' for defaults

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in source.
    """
    if args is None:
        args = cf.config_args()
    src_code_dir = os.path.join(args.working_dir, args.code_path, args.src_path)
    sys.path.append(src_code_dir)
    src_module = __import__(module)
    SrcClass = src_module.get_SrcClass(args)
    version_dict = compare_versions(SrcClass, args)
    for alias in version_dict:
        iu.import_filemeta(version_dict[alias], args)
    return version_dict

def main_parse_args():
    """Processes command line arguments.

    Expects three positional arguments(start_step, deploy_loc, run_mode) and
    a number of optional arguments. If arguments are missing, supplies default
    values.

    Returns:
        Namespace: args as populated namespace
    """
    parser = ArgumentParser()
    parser.add_argument('module', help='select SrcClass to check, e.g. dip')
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main_parse_args()
    check(args.module, args)
