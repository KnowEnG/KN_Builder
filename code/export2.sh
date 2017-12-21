#!/bin/bash

set -u

## extract Property node maps
for CLASS1 in Property; do
    for line in `grep $CLASS1 $KNP_EXPORT_DIR/directories.txt | sed 's#\t#/#g'` ; do
        echo $line;
        CLASS=$(echo $line | cut -f1 -d/)
        TAXON=$(echo $line | cut -f2 -d/)
        ETYPE=$(echo $line | cut -f3 -d/)
        grep Property $KNP_EXPORT_DIR/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.node_map > $KNP_EXPORT_DIR/$CLASS/$TAXON/$ETYPE/$TAXON.$ETYPE.pnode_map
    done
done;
