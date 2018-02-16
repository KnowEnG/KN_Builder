set -eu

# default parameter values
#KNP_DATA_PATH='local_pipe'
#KNP_MYSQL_HOST='knowcluster01.knoweng.org'
#KNP_MYSQL_PORT='3306'
#KNP_MYSQL_USER='root'
#KNP_MYSQL_PASS='KnowEnG'
#KNP_REDIS_HOST='knowcluster01.knoweng.org'
#KNP_REDIS_PORT='6379'
#KNP_REDIS_PASS='KnowEnG'
VERBOSE='COUNTS'

KNP_FILE_TYPE="*json"
KNP_SRC='dip'
KNP_ALIAS='PPI'
KNP_CHUNK='1'

# command line parameters
KNP_DATA_PATH=$1
VERBOSE=$2
KNP_MYSQL_HOST=$3
KNP_REDIS_HOST=$4
KNP_MYSQL_PORT=$5
KNP_REDIS_PORT=$6

shopt -s extglob

FILE_CTR=0
echo -e "tnum\ttype\tsnum\tsource\tfile\tempty\ttime\tlines"
for KNP_FILE_TYPE in "*/file_metadata.json" "*/*.*.txt" "*.json" \
    "*/!(*file_metadata).json" "*/!(*unique).raw_line.*" "*/!(*unique).node.*" \
    "*/*.unique.node.*" "*/!(*unique).node_meta.*" "*/*.unique.node_meta.*" \
    "*/chunks/!(*unique).raw_line.*" "*/chunks/*.unique.raw_line.*" \
    "*/chunks/*.table.*" "*/chunks/!(*unique).edge_meta.*" \
    "*/chunks/*.unique.edge_meta.*" "*/chunks/!(*unique).node.*" \
    "*/chunks/*.unique.node.*" "*/chunks/!(*unique).node_meta.*" \
    "*/chunks/*.unique.node_meta.*" "*/chunks/!(*unique).edge.*" \
    "*/chunks/*.unique.edge.*" "*/chunks/!(*unique).status.*" \
    "*/chunks/*.unique.status.*" "*/chunks/*.unique.edge2line.*"; do
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

    for KNP_SRC in ensembl id_map ppi biogrid blast dip enrichr go \
        humannet intact kegg msigdb pathcom pfam_prot reactome stringdb; do
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
                    lines=`cat $KNP_DATA_PATH/$KNP_SRC/$KNP_FILE_TYPE | wc -l`
                fi
            fi
            break
        done;
        echo -e "$FILE_CTR\t$KNP_FILE_TYPE\t$SRC_CTR\t$KNP_SRC\t$files\t$zeros\t$mins\t$lines"
    done;
    echo ""
done;
echo ""
CMD="redis-cli -h $KNP_REDIS_HOST -p $KNP_REDIS_PORT -a $KNP_REDIS_PASS info | grep keys= | cut -f1 -d',' |  cut -f2 -d':'"
    echo -n Redis Keys$'\t'
    eval "$CMD"
CMD='mysql -h '$KNP_MYSQL_HOST' --port '$KNP_MYSQL_PORT'  -u'$KNP_MYSQL_USER' -p'$KNP_MYSQL_PASS' --execute "
    SELECT \"species\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.species ;
    SELECT \"edge_type\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge_type UNION
    SELECT \"node_type\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_type UNION
    SELECT \"all_mappings\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.all_mappings UNION
    SELECT \"node\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node UNION
    SELECT \"raw_file\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.raw_file UNION
    SELECT \"raw_line\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.raw_line UNION
    SELECT \"node_meta\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_meta UNION
    SELECT \"node_species\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.node_species UNION
    SELECT \"status\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.status UNION
    SELECT \"edge2line\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge2line UNION
    SELECT \"edge\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge UNION
    SELECT \"edge_meta\" AS table_name, COUNT(*) AS exact_row_count FROM KnowNet.edge_meta
"'
    echo MySQL Tables
    eval "$CMD"

