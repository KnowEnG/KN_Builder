class SrcClass(object):
    'super class for sources'
    def __init__(self, src_name, base_url, aliases):
        self.name = src_name
        self.url = base_url
        self.version = "unknown"
        self.aliases = aliases
        
    def get_source_version(self):
        pass

    def get_source_version_date(self):
        pass
    
    def get_local_file_info(self):
        pass

    def get_remote_file_size(remote_url):
        pass

    def get_remote_file_modified(self):
        pass


def compare_versions(srcObj):
    """
    compare_versions(srcObj) -> dict
    
    Returns dictionary of results of checking operations for each alias of the source including source, alias, alias_info, remote_url, remote_date, remote_version, remove_size, local_file_name, local_file_exists, fetch_needed.
    """
    pass

def check_local_file_exists(local_filename):
    """
    check_local_file_exists(filename) -> bool
    
    Returns True if file exists at locations specified by local_filename, False otherwise.
    """
    pass

