DATADIR=$1
for i in "*json" "*/file_metadata.json" "*/*json" \
    "*/*rawline*" "*/chunks/*rawline*" "*/*.node_meta.*" \
    "*/chunks/*.node_meta.*" "*/chunks/*.edge_meta.*" \
    "*/chunks/*unique_edge_meta*" "*/chunks/*.edge.*" "*/chunks/*status*" \
    "*/chunks/*.conv.*" "*/chunks/*unique_conv*" \
    "*/chunks/*unique_edge2line*"; do
    CMD="ls $DATADIR/*/$i | wc -l"
    echo -n $i$'\t'
    eval "$CMD"
    for j in biogrid blast dip ensembl go humannet id_map intact kegg msigdb \
        pfam ppi reactome species stringdb; do
        CMD2="ls $DATADIR/$j/$i | wc -l; find  $DATADIR/$j/$i -type f -empty"
        echo -n $'\t'$j$'\t'
        for f in $DATADIR/$j/$i; do
            [ -e "$f" ] && eval "$CMD2" || echo "-"
            break
        done;
    done;
done;
