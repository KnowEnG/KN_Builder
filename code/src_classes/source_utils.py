from urllib.request import urlopen
from os import path
from time import strptime, mktime

class SrcClass(object):
    'super class for sources'
    def __init__(self, src_name, base_url, aliases):
        self.name = src_name
        self.url_base = base_url
        self.version = dict()
        self.aliases = aliases
        
    def get_source_version(self):
        """Returns the source version information. 
            By default, returns the empty string."""
        return ''

    def get_source_version_date(self):
        pass
    
    def get_local_file_info(self, alias):
        """Returns a dictionary contianing the local file information for 
        source:alias which includes the local file name and a boolean that is 
        True if the file exists. If the file does exist, the dictionary also 
        contains the local file size and modified date"""
        d_dir = '/workspace/apps/P1_source_check/raw_downloads/'
        file = d_dir + self.name + '.' + alias + '.txt'
        local_dict = dict()
        local_dict['local_file_name'] = file
        local_dict['local_file_exists'] = \
            check_local_file_exists(file)
        if not local_dict['local_file_exists']:
            return local_dict
        local_dict['local_size'] = path.getsize(file)
        local_dict['local_date'] = path.getmtime(file)
        return local_dict

    def get_remote_file_size(self, remote_url):
        """Returns the remote file size as described in the headers of 
        remote_url"""
        response = urlopen(remote_url)
        return response.headers['content-length']

    def get_remote_file_modified(self, remote_url):
        """Returns the remote file modified date as described in the headers of
        remote url"""
        response = urlopen(remote_url)
        return response.headers['last-modified']
    
    def get_remote_url(self, alias):
        """Returns the url for fetching a file. By default this is the base 
        url"""
        return self.url_base
        

def compare_versions(srcObj):
    """
    compare_versions(srcObj) -> dict
    
    Returns dictionary of results of checking operations for each alias of 
    the source including source, alias, alias_info, remote_url, remote_date, 
    remote_version, remote_size, local_file_name, local_file_exists, and
    fetch_needed.
    """
    version_dict = dict()
    local_dict = dict()
    for alias in srcObj.aliases:
        local_dict[alias] = srcObj.get_local_file_info(alias)
        version_dict[alias] = dict()
        version_dict[alias]['alias_info'] = srcObj.aliases[alias]
        version_dict[alias]['remote_url'] = srcObj.get_remote_url(alias)
        version_dict[alias]['remote_date'] = \
            srcObj.get_remote_file_modified(alias)
        version_dict[alias]['remote_version'] = \
            srcObj.get_source_version(alias)
        version_dict[alias]['remote_size'] = srcObj.get_remote_file_size(alias)
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
    
    return version_dict

def check_local_file_exists(local_file_name):
    """
    check_local_file_exists(filename) -> bool
    
    Returns True if file exists at locations specified by local_file_name, 
    False otherwise.
    """
    return path.isfile(local_file_name)
