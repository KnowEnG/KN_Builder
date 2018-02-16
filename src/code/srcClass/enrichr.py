"""Extension of utilities.py to provide functions required to check the
version information of enrichr and determine if it needs to be updated.

Classes:
    Enrichr: Extends the SrcClass class and provides the static variables and
        enrichr specific functions required to perform a check on enrichr.

Functions:
    get_SrcClass: returns a Enrichr object
    main: runs compare_versions (see utilities.py) on a Enrichr object
"""
import csv
import hashlib
import os
import config_utilities as cf
import table_utilities as tu
from check_utilities import SrcClass, compare_versions

def get_SrcClass(args):
    """Returns an object of the source class.

    This returns an object of the source class to allow access to its functions
    if the module is imported.

    Args:

    Returns:
        class: a source class object
    """
    return Enrichr(args)

class Enrichr(SrcClass):
    """Extends SrcClass to provide enrichr specific check functions.

    This Enrichr class provides source-specific functions that check the
    enrichr version information and determine if it differs from the current
    version in the Knowledge Network (KN).

    Attributes:
        see utilities.SrcClass
    """
    def __init__(self, args=cf.config_args()):
        """Init a Enrichr with the staticly defined parameters.

        This calls the SrcClass constructor (see utilities.SrcClass)
        """
        name = 'enrichr'
        url_base = ('http://amp.pharm.mssm.edu/Enrichr/'
                    'geneSetLibrary?mode=text&libraryName=')
        aliases = {
            "Achilles_fitness_decrease": "achilles_genetic_fitness::ach_dn",
            "Achilles_fitness_increase": "achilles_genetic_fitness::ach_up",
            "Aging_Perturbations_from_GEO_down": "GEO_expression_set::aging_dn",
            "Aging_Perturbations_from_GEO_up": "GEO_expression_set::aging_up",
            "Allen_Brain_Atlas_down": "allen_brain_atlas_signature::aba_dn",
            "Allen_Brain_Atlas_up": "allen_brain_atlas_signature::aba_up",
            "Cancer_Cell_Line_Encyclopedia": "enrichr_cell_signature::ccle",
            "ChEA_2015": "enrichr_ChIP_gene_set::chea",
            "dbGaP": "enrichr_phenotype_signature::dbgap",
            "Disease_Perturbations_from_GEO_down": "GEO_expression_set::dis-pert_dn",
            "Disease_Perturbations_from_GEO_up": "GEO_expression_set::dis-pert_up",
            "Disease_Signatures_from_GEO_down_2014": "GEO_expression_set::dis-sig_dn",
            "Disease_Signatures_from_GEO_up_2014": "GEO_expression_set::dis-sig_up",
            "Drug_Perturbations_from_GEO_2014": "GEO_expression_set::drug_pert",
            "Drug_Perturbations_from_GEO_down": "GEO_expression_set::drug_dn",
            "Drug_Perturbations_from_GEO_up": "GEO_expression_set::drug_up",
            "ENCODE_Histone_Modifications_2015": "enrichr_ChIP_gene_set::ENCODE_HM",
            "ENCODE_TF_ChIP-seq_2015": "enrichr_ChIP_gene_set::ENCODE_TF",
            "Epigenomics_Roadmap_HM_ChIP-seq": "enrichr_ChIP_gene_set::ER_HM",
            "ESCAPE": "ESCAPE_gene_set::ESCAPE",
            "GeneSigDB": "genesigdb_gene_signature::gsigdb",
            "GTEx_Tissue_Sample_Gene_Expression_Profiles_down": "enrichr_tissue_signature::GTEx_dn",
            "GTEx_Tissue_Sample_Gene_Expression_Profiles_up": "enrichr_tissue_signature::GTEx_up",
            "HMDB_Metabolites": "HMDB_metabolite_signatures::HMDB",
            "Human_Gene_Atlas": "enrichr_tissue_signature::HGA",
            "Human_Phenotype_Ontology": "enrichr_phenotype_signature::HPO",
            "KEA_2015": "KEA_kinase_signatures::KEA",
            "Kinase_Perturbations_from_GEO_down": "GEO_expression_set::kinase_dn",
            "Kinase_Perturbations_from_GEO_up": "GEO_expression_set::kinase_up",
            "Ligand_Perturbations_from_GEO_down": "GEO_expression_set::ligand_dn",
            "Ligand_Perturbations_from_GEO_up": "GEO_expression_set::ligand_up",
            "LINCS_L1000_Chem_Pert_down": "LINCS_down_set::LINCS_dn",
            "LINCS_L1000_Chem_Pert_up": "LINCS_up_set::LINCS_up",
            "MCF7_Perturbations_from_GEO_down": "GEO_expression_set::MCF7_dn",
            "MCF7_Perturbations_from_GEO_up": "GEO_expression_set::MCF7_up",
            "MGI_Mammalian_Phenotype_2013": "enrichr_phenotype_signature::MGI",
            "MGI_Mammalian_Phenotype_Level_3": "enrichr_phenotype_signature::MGI_L3",
            "MGI_Mammalian_Phenotype_Level_4": "enrichr_phenotype_signature::MGI_L4",
            "Microbe_Perturbations_from_GEO_down": "GEO_expression_set::microbe_dn",
            "Microbe_Perturbations_from_GEO_up": "GEO_expression_set::microbe_up",
            "Mouse_Gene_Atlas": "enrichr_phenotype_signature::MGA",
            "NCI-60_Cancer_Cell_Lines": "enrichr_cell_signature::NCI",
            "NCI-Nature_2016": "enrichr_pathway::NCI",
            "NURSA_Human_Endogenous_Complexome": "PPI_complex::NHEC",
            "OMIM_Disease": "enrichr_phenotype_signature::OMIM-dis",
            "OMIM_Expanded": "enrichr_phenotype_signature::OMIM-exp",
            "Panther_2016": "panther_classification::Panther",
            "PPI_Hub_Proteins": "PPI_hub::",
            "SILAC_Phosphoproteomics": "SILAC_phosphoproteomics::SILCA",
            "Single_Gene_Perturbations_from_GEO_down": "GEO_expression_set::gene_dn",
            "Single_Gene_Perturbations_from_GEO_up": "GEO_expression_set::gene_up",
            "TargetScan_microRNA": "TargetScan_microRNA::TargetScan",
            "TF-LOF_Expression_from_GEO": "GEO_expression_set::TF-LOF",
            "Tissue_Protein_Expression_from_Human_Proteome_Map": "enrichr_tissue_signature::HPM",
            "Tissue_Protein_Expression_from_ProteomicsDB": "enrichr_tissue_signature::PDB",
            "Virus_Perturbations_from_GEO_down": "GEO_expression_set::virus_dn",
            "Virus_Perturbations_from_GEO_up": "GEO_expression_set::virus_up",
            "WikiPathways_2016": "enrichr_pathway::WikiPath"
        }
        super(Enrichr, self).__init__(name, url_base, aliases, args)
        self.chunk_size = 500
        self.date_modified = 'unknown'

        self.source_url = "http://amp.pharm.mssm.edu/Enrichr/"
        self.image = "https://lw-static-files.s3.amazonaws.com/public/logos/2688.png"
        self.reference = ("Kuleshov MV, Jones MR, Rouillard AD, et al. Enrichr: a comprehensive "
                          "gene set enrichment analysis web server 2016 update. Nucleic Acids Res. "
                          "2016;44(W1):W90-7.")
        self.pmid = 27141961
        self.license = ('Enrichr\'s web-based tools and services are free for academic, non-profit '
                        'use, but for commercial uses please contact <a '
                        'href="http://www.ip.mountsinai.org/">MSIP</a> for a license.')

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
        url = self.url_base + alias
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

        #static column values
        alias = version_dict['alias']
        source = version_dict['source']
        mouse_aliases = ["MGI_Mammalian_Phenotype_2013", \
                         "MGI_Mammalian_Phenotype_Level_3",\
                         "MGI_Mammalian_Phenotype_Level_4", "Mouse_Gene_Atlas"]
        n1type = 'property'
        n_type = 'Property'
        n1spec = '0'
        n1hint = source + '_' + alias
        n2type = 'gene'
        if alias in mouse_aliases:
            n2spec = '10090'
            n2hint = 'MGI'
        else:
            n2spec = '9606'
            n2hint = 'HGNC'
        (et_hint, node_prefix) = self.aliases[alias].split('::')
        score = 1

        if alias == 'PPI_Hub_Proteins':
            n1type = 'gene'
            n1spec = '9606'
            n1hint = 'HGNC'


        with open(raw_line, encoding='utf-8') as infile, \
            open(table_file, 'w') as edges,\
            open(n_meta_file, 'w') as n_meta, \
            open(node_file, 'w') as nfile:
            edge_writer = csv.writer(edges, delimiter='\t', lineterminator='\n')
            n_meta_writer = csv.writer(n_meta, delimiter='\t', lineterminator='\n')
            n_writer = csv.writer(nfile, delimiter='\t', lineterminator='\n')
            for line in infile:
                line = line.replace('"', '').strip().split('\t')
                #line = re.split('\s{2,}', line)
                if len(line) == 1:
                    continue
                chksm = line[0]
                raw = line[3:]
                n1_orig_name = raw[0]
                n1_kn_name = n1_orig_name
                if alias != 'PPI_Hub_Proteins':
                    n1_kn_name = cf.pretty_name(node_prefix + '_'+ n1_orig_name)
                    n_meta_writer.writerow([n1_kn_name, 'orig_desc', n1_orig_name])
                    n_writer.writerow([n1_kn_name, n1_kn_name, n_type])
                for n2_id in raw[1:]:
                    n2_id = n2_id.split(',')[0]
                    if n2_id == '':
                        continue
                    hasher = hashlib.md5()
                    hasher.update('\t'.join([chksm, n1_kn_name, n1hint, n1type, n1spec,\
                        n2_id, n2hint, n2type, n2spec, et_hint,\
                        str(score)]).encode())
                    t_chksum = hasher.hexdigest()
                    edge_writer.writerow([chksm, n1_kn_name, n1hint, n1type, n1spec, \
                            n2_id, n2hint, n2type, n2spec, et_hint, score, \
                            t_chksum])

        if alias != 'PPI_Hub_Proteins':
            outfile = n_meta_file.replace('node_meta', 'unique.node_meta')
            tu.csu(n_meta_file, outfile)
            outfile = node_file.replace('node', 'unique.node')
            tu.csu(node_file, outfile)
        else:
            os.remove(n_meta_file)
            os.remove(node_file)


def main():
    """Runs compare_versions (see utilities.compare_versions) on a Enrichr
    object

    This runs the compare_versions function on a Enrichr object to find the
    version information of the source and determine if a fetch is needed. The
    version information is also printed.

    Returns:
        dict: A nested dictionary describing the version information for each
            alias described in Enrichr.
    """
    compare_versions(Enrichr())

if __name__ == "__main__":
    main()
