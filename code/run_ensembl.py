#This is a quick and dirty way to run all of the ensembl imports

import config_utilities as cf
import ensembl as ens
import fetch_utilities as fu
import check_utilities as cu
import os

cu.check('ensembl')
ensembl_dir = os.path.join(cf.DEFAULT_LOCAL_BASE, cf.DEFAULT_DATA_PATH,\
    'ensembl')
os.chdir(ensembl_dir)
for alias in os.listdir('.'):
    print('Processing ' + alias)
    os.chdir(alias)
    fu.main('file_metadata.json')
    ens.db_import('file_metadata.json')
    os.chdir('..')