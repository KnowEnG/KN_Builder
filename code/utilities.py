"""Provides all of the utility files needed to check if a source has updated.
Also contains the parent source class: SrcClass"""
import urllib.request
import os
import json

DIR = '../raw_downloads/'

class SrcClass(object):
    """super class for sources"""
    def __init__(self, src_name, base_url, aliases):
        self.name = src_name
        self.url_base = base_url
        self.version = dict()
        self.aliases = aliases

    def get_source_version(self, alias):
        """Returns the source version information.
            By default, returns the empty string."""
        return ''

    def get_source_version_date(self, alias):
        """Returns the release date of the source:alias version"""
        return ''

    def get_local_file_info(self, alias):
        """Returns a dictionary contianing the local file information for
        source:alias which includes the local file name and a boolean that is
        True if the file exists. If the file does exist, the dictionary also
        contains the local file size and modified date"""
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
        """Returns the remote file size as described in the headers of
        remote_url"""
        response = urllib.request.urlopen(remote_url)
        return response.headers['content-length']

    def get_remote_file_modified(self, remote_url):
        """Returns the remote file modified date as described in the headers of
        remote url"""
        response = urllib.request.urlopen(remote_url)
        return response.headers['last-modified']

    def get_remote_url(self, alias):
        """Returns the url for fetching a file. By default this is the base
        url"""
        return self.url_base


def compare_versions(src_obj):
    """
    compare_versions(src_obj) -> dict

    Returns dictionary of results of checking operations for each alias of
    the source including source, alias, alias_info, remote_url, remote_date,
    remote_version, remote_size, local_file_name, local_file_exists, and
    fetch_needed.
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
    with open(f_dir + src_obj.name + '_check.json', 'w') as outfile:
        json.dump(version_dict, outfile, indent=4, sort_keys=True)
    print(json.dumps(version_dict, indent=4, sort_keys=True))
    return version_dict
