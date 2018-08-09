# KN_Builder

Fetch and parse source files to construct the KnowEnG Knowledge Network

# Running Manually

- **Enter the Docker container**
```console
docker run -it -w=`pwd` -v `pwd`:`pwd` knoweng/kn_builder:latest
```


- **Run command within the Docker container**
```console
python3 /kn_builder/code/job_status.py --ens_species homo_sapiens \
    --src_classes stringdb,,reactome,,enrichr,,biogrid
```

