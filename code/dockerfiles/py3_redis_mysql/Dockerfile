############################################################
# Dockerfile to build py3_redis_mysql
############################################################

# Set the base image to python v3
FROM python:3.4-slim

# File Author / Maintainer
MAINTAINER Charles Blatti

# Update the repository sources list
RUN apt-get update && apt-get install -y \
    curl \
    time \
    rsync \
    wget \
    mysql-client \
    python3-pip

RUN pip3 install https://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.tar.gz
RUN pip3 install redis \
    requests \
    line_profiler

# Set default contain command on run
CMD /bin/bash

# Set container execution behavior
# ENTRYPOINT
