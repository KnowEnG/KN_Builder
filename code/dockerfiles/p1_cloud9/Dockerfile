############################################################
# Dockerfile to build p1_cloud9
############################################################

# Set the base image 
FROM sapk/cloud9

# File Author / Maintainer
MAINTAINER Charles Blatti

# Update the repository sources list
RUN apt-get update && apt-get install -y time \
    wget \
    curl \
    man \
    git \
    lxc \
    libsystemd-journal0 \
    bash-completion \
    sshfs \
    vim \
    mysql-client \
    redis-tools \
    python-dev \
    python-pip \
    python-tables \
    python3 \
    python3-pip \
    r-base \
    r-base-dev

# pip3 install for db connectors
RUN pip3 install https://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.tar.gz
RUN pip3 install redis \
    pylint

# pip installs for lincs
RUN pip install s3cmd \
    numpy \
    pandas \
    requests \
    blessings

# copy lincs package to standard path
ADD cmap /usr/local/lib/python2.7/dist-packages/

# Set default contain command on run
CMD /bin/bash

# Set container execution behavior
# ENTRYPOINT