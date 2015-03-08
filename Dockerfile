# Latest Ubuntu LTS
FROM registry
MAINTAINER milaw <gmilaw@gmail.com>

# Update
RUN apt-get update
RUN apt-get -y upgrade

# Install pip
RUN apt-get -y install swig python-pip

RUN apt-get -y install python-dev liblzma-dev libevent1-dev gcc python-dev

RUN pip install blist \
	lz4 \
	cassandra-driver

# Install 
RUN pip install docker-registry-driver-cassandra

ADD . /docker-registry-driver-cassandra

ENV DOCKER_REGISTRY_CONFIG /docker-registry-driver-cassandra/config/config.yml
ENV SETTINGS_FLAVOR cassandra