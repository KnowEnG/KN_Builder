tail  -n+2 directories.txt | awk '{print $3"\t"$1"\t"$2}' | sort | uniq > /tmp/t1
tail  -n+2 edge_type.txt | cut -f1,10 | sort | uniq > /tmp/t2
join /tmp/t1 /tmp/t2 | awk '{print $2"\t"$4"\t"$3"\t"$1"\t"$2"/"$3"/"$1"/"$3"."$1".node_map"}' | sort > /tmp/t3

rm /tmp/list.txt

for NT in `cut -f1 /tmp/t3 | sort | uniq` ALL; do
  NTgrep=$NT
  NTcmd=`grep -P $NT /tmp/t3 | cut -f2 | sort | uniq`
  if [ $NT == "ALL" ]; then
    NTgrep="\t"
    NTcmd=''
  fi
  for SC in $NTcmd ALL; do
    SCgrep=$SC
    SCcmd=`grep -P $SC /tmp/t3 | grep -P $NTgrep | cut -f4 | sort | uniq`
    if [ $SC == "ALL" ]; then
      SCgrep="\t"
      SCcmd=''
    fi
    for ET in $SCcmd ALL; do
      ETgrep=$ET
      if [ $ET == "ALL" ]; then
        ETgrep="\t"
      fi
      ETcmd=`grep -P $ETgrep /tmp/t3 | grep -P $SCgrep | grep -P $NTgrep | cut -f3 | sort | uniq`
      for SP in $ETcmd ALL; do
      SPgrep=$SP
      if [ $SP == "ALL" ]; then
        SPgrep="\t"
      fi

        Fnodes=`grep -P $SPgrep /tmp/t3 | grep -P $ETgrep | grep -P $SCgrep | grep -P $NTgrep | cut -f5 | sort | uniq`
        Fct=`echo $Fnodes | sed 's# #\n#g' | wc -l`
        Fedges=`echo $Fnodes | sed 's#.node_map#.edge#g'`
        Fpnodes=`echo $Fnodes | sed 's#.node_map#.pnode_map#g'`
        # number of nodes
        Nnodes=`cut -f2 $Fnodes | sort | uniq | wc -l`
        # number of genes
        Ngnodes=`grep -P "\tGene\t" $Fnodes | cut -f2 | sort | uniq | wc -l`
        # number of sources
        Nsources=`cut -f5 $Fedges | sort | uniq | wc -l`
        # number of edges
        Nedges=`wc -l $Fedges | awk '{print $1}' | sort -rg | head -n1`

        Npnodes=0
        # number of properties
        if [ $NT != "Gene" ]; then
          Npnodes=`cut -f2 $Fpnodes | sort | uniq | wc -l`
        fi

        #OUTSTR="$NT $SC $ET $SP $Fct $Nnodes"
        OUTSTR="$NT $SC $ET $SP $Fct $Nnodes $Ngnodes $Npnodes $Nedges $Nsources"
        echo $OUTSTR
        echo $OUTSTR >> /tmp/list.txt

      done
    done
  done
done


