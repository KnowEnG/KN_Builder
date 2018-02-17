# KN_Builder

Fetch and parse source files to construct the KnowEnG Knowledge Network

# Running Manually

- **Enter the Docker container**
```console
docker run -it -w=`pwd` -v `pwd`:`pwd` cblatti3/kn_builder:latest
```

- **Run command within the Docker container**
```console
python3 /kn_builder/code/job_status.py --species homo_sapiens \
    --source stringdb reactome enrichr biogrid --build_name hsap-1802
```

