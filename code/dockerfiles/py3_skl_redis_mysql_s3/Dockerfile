############################################################
# Dockerfile to build py3_skl_redis_mysql_s3
############################################################

# Set the base image to python v3
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER Charles Blatti

RUN apt-get update && apt-get -y install \
    build-essential \
    gfortran \
    pkg-config \
    libatlas-dev \
    libatlas3gf-base \
    python3-dev \
    python3-setuptools \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-matplotlib \
    python3-numexpr \
    git-core \
    mysql-client \
    time \
    curl \
    rsync \
    wget

RUN sudo update-alternatives --set libblas.so.3 \
    /usr/lib/atlas-base/atlas/libblas.so.3
RUN sudo update-alternatives --set liblapack.so.3 \
    /usr/lib/atlas-base/atlas/liblapack.so.3

RUN wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

RUN pip3 install --user --install-option="--prefix=" -U scikit-learn

RUN pip3 install https://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.tar.gz
RUN pip3 install redis \
    requests \
    awscli \
    line_profiler

ENV PYTHONUNBUFFERED 1

# Set default contain command on run
CMD /bin/bash

# Set container execution behavior
# ENTRYPOINT
