"""Utiliites for checking if a source needs to be updated in the Knowledge
Network (KN).

Classes:
    SrcClass: Extends the object class and serves as the base class for each
        supported source in the KN.

Functions:
    compare_versions(SrcClass) -> dict: takes a SrcClass object and returns a
        dictionary containing the most recent file version information and if
        a fetch is required

Variables:
    DIR: the relative location of the raw_downloads directory
"""

import urllib.request
import os
import json

DIR = '../raw_downloads/'

class SrcClass(object):
    """Base class to be extended by each supported source in KnowEnG.

    This SrcClass provides default functions that should be extended
    or overridden by any source which is added to the Knowledge Network (KN).

    Attributes:
        name (str): The name of the remote source to be included in the KN.
        url_base (str): The base url of the remote source, which may need 
            additional processing to provide an actual download link (see
            get_remote_url).
        version (dict): The release version of each alias in the source.
        aliases (dict): A dictionary with subsets of the source which will be 
            included in the KN  as the keys (e.g. different species, data 
            types, or interaction types), and a short string with information 
            about the alias as the value.
    """
    
    def __init__(self, src_name, base_url, aliases, version=dict()):
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
            version (dict): The release version of each alias in the source.
                Default empty dictionary if not provided by the extending
                class.
        """
        self.name = src_name
        self.url_base = base_url
        self.aliases = aliases
        self.version = version

    def get_source_version(self, alias):
        """Return the release version of the remote source:alias.

        This returns the release version of the remote source for a specific
        alias. This value will be the same for every alias unless the
        the alias can have a different release version than the source
        (this will be source dependent). This value is stored in the 
        self.version dictionary object. If the value does not already,
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
        will always contain the following keys: 
            'local_file_name' (str): the path to where the local file
            'local_file_exists' (bool): boolean if file exists at path
                indicated by 'local_file_name'
        and will also conatin the following if 'local_file_exists' is True:
            'local_size' (int): size of local file in bytes
            'local_date' (float): time of last modification time of local file
                in seconds since the epoch

        Args:
            alias (str): An alias defined in self.aliases.

        Returns:
            dict: The local file information for a given source alias.
        """            

        f_dir = DIR + self.name + '/'
        file = f_dir + self.name + '.' + alias + '.txt'
        local_dict = dict()
        local_dict['local_file_name'] = file
        local_dict['local_file_exists'] = os.path.isfile(file)
        if not local_dict['local_file_exists']:
            return local_dict
        local_dict['local_size'] = os.path.getsize(file)
        local_dict['local_date'] = os.path.getmtime(file)
        return local_dict

    def get_remote_file_size(self, remote_url):
        """Return the remote file size.

        This returns the remote file size as specificied by the
        'content-length' page header.

        Args:
            remote_url (str): The url of the remote file to get the size of.

        Returns:
            int: The remote file size in bytes.
        """
        response = urllib.request.urlopen(remote_url)
        return float(response.headers['content-length'])

    def get_remote_file_modified(self, remote_url):
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
        response = urllib.request.urlopen(remote_url)
        time_str = response.headers['last-modified']
        time_format = "%a, %d %b %Y %H:%M:%S %Z"
        return time.mktime(time.strptime(time_str, time_format))

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


def compare_versions(src_obj):
    """Return a dictionary with the version information for each alias in the
    source.

    This returns a nested dictionary describing the version information of each
    alias in the source. The version information is also printed. For each
    alias the following keys are defined:
        'alias_info' (str): A short string with information about the alias.
        'remote_url' (str): See get_remote_url.
        'remote_date' (float): See get_remote_file_modified.
        'remote_version' (str): See get_source_version.
        'local_file_name' (str): See get_local_file_info.
        'local_file_exists' (bool): See get_local_file_info.
        'fetch_needed' (bool): True if file needs to be downloaded from remote
            source. A fetch will be needed if the local file does not exist,
            or if the local and remote files have different date modified or 
            file sizes.

    Args:
        src_obj (SrcClass): A SrcClass object for which the comparison should
            be performed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in src_obj.
    """
    version_dict = dict()
    local_dict = dict()
    for alias in src_obj.aliases:
        local_dict[alias] = src_obj.get_local_file_info(alias)
        version_dict[alias] = dict()
        version_dict[alias]['alias_info'] = src_obj.aliases[alias]
        version_dict[alias]['remote_url'] = src_obj.get_remote_url(alias)
        version_dict[alias]['remote_date'] = \
            src_obj.get_remote_file_modified(alias)
        version_dict[alias]['remote_version'] = \
            src_obj.get_source_version(alias)
        version_dict[alias]['remote_size'] = src_obj.get_remote_file_size(alias)
        version_dict[alias]['local_file_name'] = \
            local_dict[alias]['local_file_name']
        version_dict[alias]['local_file_exists'] = \
            local_dict[alias]['local_file_exists']

        if not local_dict[alias]['local_file_exists']:
            version_dict[alias]['fetch_needed'] = True
            continue

        l_size = int(local_dict[alias]['local_size'])
        r_size = int(version_dict[alias]['remote_size'])
        l_date = float(local_dict[alias]['local_date'])
        r_date = float(version_dict[alias]['remote_date'])

        if l_size != r_size:
            version_dict[alias]['fetch_needed'] = True
        elif l_date < r_date:
            version_dict[alias]['fetch_needed'] = True
        else:
            version_dict[alias]['fetch_needed'] = False

    f_dir = DIR + src_obj.name + '/'
    os.makedirs(f_dir, exist_ok=True)
    with open(f_dir + src_obj.name + '_check.json', 'w') as outfile:
        json.dump(version_dict, outfile, indent=4, sort_keys=True)
    print(json.dumps(version_dict, indent=4, sort_keys=True))
    return version_dict
