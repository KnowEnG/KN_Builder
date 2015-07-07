from source_utils import *

class Go(SrcClass):
    def __init__(self):
        name = 'go'
        url = 'http://geneontology.org//gene-associations/'
        aliases = {
            "fb": "Drosophila melanogaster",
            "goa_human": "Homo sapiens",
            "mgi": "Mus musculus",
            "obo": "ontology",
            "sgd": "Saccharomyces cerevisiae",
            "tair": "Arabidopsis thaliana",
            "wb": "Caenorhabditis elegans"
        }

        super(Go, self).__init__(name, url, aliases)
        
    def get_source_version(self):
        version_info_url = ''
        version_reg_ex = ''
        pass

if __name__ == "__main__":
    compare_versions(Go())