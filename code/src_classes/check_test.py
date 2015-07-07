from source_utils import compare_versions
from stringdb import Stringdb
from pprint import pprint

d = compare_versions(Stringdb())
pprint(d, width=1)