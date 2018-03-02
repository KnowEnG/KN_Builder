#!/bin/bash

set -u

KNP_EXPORT_DIR=$KNP_WORKING_DIR/$KNP_EXPORT_PATH
mkdir -p $KNP_EXPORT_DIR
cp $KNP_CODE_DIR/mysql/edge_type.txt $KNP_EXPORT_DIR

## add gene maps
cp $KNP_WORKING_DIR/$KNP_DATA_PATH/id_map/species/species.txt $KNP_EXPORT_DIR/species.txt
for TAXON in `cut -f1 $KNP_EXPORT_DIR/species.txt `; do
    echo $TAXON;
    mkdir -p $KNP_EXPORT_DIR/Species/$TAXON;
    mysql -h$KNP_MYSQL_HOST -u$KNP_MYSQL_USER -p$KNP_MYSQL_PASS -P$KNP_MYSQL_PORT -DKnowNet -e "\
        SELECT ns.node_id \
        FROM node_species ns \
        WHERE ns.taxon = $TAXON \
        ORDER BY ns.node_id" \
        | tail -n +2 > $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
        LANG=C.UTF-8 python3 $KNP_CODE_DIR/conv_utilities.py -mo LIST \
            -rh $KNP_REDIS_HOST -rp $KNP_REDIS_PORT -t $TAXON \
            $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
        rm $KNP_EXPORT_DIR/Species/$TAXON/$TAXON.glist;
done

## add subnetworks
mysql -h$KNP_MYSQL_HOST -p$KNP_MYSQL_PASS -u$KNP_MYSQL_USER -P$KNP_MYSQL_PORT -DKnowNet -e "\
   SELECT et.n1_type, ns2.taxon, e.et_name, count(1) \
   FROM edge e, edge_type et, node_species ns2 \
   WHERE e.et_name=et.et_name \
   AND e.n2_id=ns2.node_id \
   GROUP BY et.n1_type, ns2.taxon, e.et_name" \
   > $KNP_EXPORT_DIR/db_contents.txt
head -n1 $KNP_EXPORT_DIR/db_contents.txt \
    > $KNP_EXPORT_DIR/directories.txt
awk -v x=125000 '$4 >= x' $KNP_EXPORT_DIR/db_contents.txt \
    | grep "^Gene" >> $KNP_EXPORT_DIR/directories.txt
awk -v x=4000 '$4 >= x' $KNP_EXPORT_DIR/db_contents.txt \
    | grep "^Property" >> $KNP_EXPORT_DIR/directories.txt
python3 $KNP_CODE_DIR/workflow_utilities.py EXPORT $KNP_CONFIG_OPTS \
    -p "$(tail -n+2 $KNP_EXPORT_DIR/directories.txt \
        | cut -f2,3 \
        | sed -e 's/\t/::/g' \
        | sed -e ':a;N;$!ba;s/\n/,,/g')"
