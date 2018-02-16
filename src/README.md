# KN_Builder

Fetch and parse source files to construct the KnowEnG Knowledge Network

# Running Manually

1. Enter the Docker container

```console
docker run -it -w='/home/ubuntu' -v `pwd`:/home/ubuntu cblatti3/kn_builder:latest
```

2. Run command within the Docker container

```console
python3 /kn_builder/job_status.py \
  --species homo_sapiens \
  --source stringdb reactome enrichr biogrid \
  --build_name hsap-1802
```

