class SrcClass(object):
    'super class for sources'
    def __init__(self, src_name, url, aliases):
        self.name = src_name
        self.url = url
        self.aliases = aliases
    def get_date(self):
        return "ERROR: Must be overridden by child class"
    def clean(self):
        return "calling " + self.name + "'s get_date returned: " + self.get_date()

def process_src(srcObj):
    print(srcObj.name, srcObj.url, srcObj.aliases)
    print(srcObj.clean())