from source_utils import *

class Dip(SrcClass):
    def __init__(self):
        name = 'dip'
        url = 'http://dip.doe-mbi.ucla.edu/dip/script/files/'
        aliases = ['PPI']
        super(Dip, self).__init__(name, url, aliases)
    def get_date(self):
        return "Today is a good day to die"

if __name__ == "__main__":
    process_src(Dip())