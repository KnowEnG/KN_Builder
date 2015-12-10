# default parameter values
KNP_LOCAL_DIR='/workspace/apps/KnowNet_Pipeline'
KNP_DATA_PATH='local_pipe'
KNP_MYSQL_HOST='knowcharles.dyndns.org'
KNP_REDIS_HOST='knowcharles.dyndns.org'
KNP_CHRONOS_URL='mmaster01.cse.illinois.edu:4400'
KNP_FILE_TYPE="*json"
KNP_SRC='dip'
KNP_ALIAS='PPI'
KNP_CHUNK='1'
VERBOSE='COUNTS'

# command line parameters
KNP_DATA_PATH=$1
VERBOSE=$2

FILE_CTR=0
for KNP_FILE_TYPE in "*/file_metadata.json" "*/*.*.txt" "*json" "*/*json" \
    "*/*rawline*" "*/*.node_meta.*" "*/chunks/*rawline*" \
    "*/chunks/*.node_meta.*" "*/chunks/*.edge_meta.*" \
    "*/chunks/*unique_edge_meta*" "*/chunks/*.edge.*" "*/chunks/*status*" \
    "*/chunks/*.conv.*" "*/chunks/*unique_conv*" \
    "*/chunks/*unique_edge2line*"; do
    FILE_CTR=$(($FILE_CTR + 1))
    files='-'
    zeros='-'
    lines='-'
    mins='-'
    for f in $KNP_DATA_PATH/*/$KNP_FILE_TYPE; do
        if [ -e "$f" ] ; then
            files=`ls $KNP_DATA_PATH/*/$KNP_FILE_TYPE | wc -l`
            zeros=`find $KNP_DATA_PATH/*/$KNP_FILE_TYPE -type f -empty | wc -l;`
            start=`find $KNP_DATA_PATH/*/$KNP_FILE_TYPE -type f -exec ls -lt {} + | tail -n 1 | awk {'print $6, $7,$8'}`
            finish=`find $KNP_DATA_PATH/*/$KNP_FILE_TYPE -type f -exec ls -lt {} + | head -n 1 | awk {'print $6, $7,$8'}`
            mins=$(( $(date -d "$finish" +"%s") / 60 - $(date -d "$start" +"%s") / 60 ))
            if [ "$VERBOSE" == "COUNTS" ]; then
                lines=`cat $KNP_DATA_PATH/*/$KNP_FILE_TYPE | wc -l`
            fi
        fi
        break
    done;
    SRC_CTR=0
    echo -e "$FILE_CTR\t$KNP_FILE_TYPE\t$SRC_CTR\tALL\t$files\t$zeros\t$mins\t$lines"

    for KNP_SRC in ensembl id_map ppi species biogrid blast dip go humannet \
        intact kegg msigdb pfam reactome stringdb; do
        SRC_CTR=$(($SRC_CTR + 1))
        files='-'
        zeros='-'
        lines='-'
        mins='-'
        for f in $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE; do
            if [ -e "$f" ] ; then
                files=`ls $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE | wc -l`
                zeros=`find $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE -type f -empty | wc -l;`
                start=`find $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE -type f -exec ls -lt {} + | tail -n 1 | awk {'print $6, $7,$8'}`
                finish=`find $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE -type f -exec ls -lt {} + | head -n 1 | awk {'print $6, $7,$8'}`
                mins=$(( $(date -d "$finish" +"%s") / 60 - $(date -d "$start" +"%s") / 60 ))
                if [ "$VERBOSE" == "COUNTS" ]; then
                    lines=`cat $KNP_DATA_PATH/*/$KNP_FILE_TYPE | wc -l`
                fi
            fi
            break
        done;
        echo -e "$FILE_CTR\t$KNP_FILE_TYPE\t$SRC_CTR\t$KNP_SRC\t$files\t$zeros\t$mins\t$lines"
    done;
    echo ""
done;
echo ""
CMD="redis-cli -h $KNP_REDIS_HOST -a KnowEnG  info | grep keys= | cut -f1 -d',' |  cut -f2 -d':'"
    echo -n Redis Keys$'\t'
    eval "$CMD"
CMD='mysql -h '$KNP_MYSQL_HOST' -uroot -pKnowEnG --execute "
    SELECT \"all_mappings\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.all_mappings UNION
    SELECT \"edge\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge UNION
    SELECT \"edge2line\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge2line UNION
    SELECT \"edge_meta\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge_meta UNION
    SELECT \"edge_type\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge_type UNION
    SELECT \"node\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node UNION
    SELECT \"node_meta\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_meta UNION
    SELECT \"node_species\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_species UNION
    SELECT \"node_type\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_type UNION
    SELECT \"raw_file\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.raw_file UNION
    SELECT \"raw_line\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.raw_line UNION
    SELECT \"species\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.species ;
"'
    echo MySQL Tables
    eval "$CMD"