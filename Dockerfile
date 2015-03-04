# Latest Ubuntu LTS
FROM ubuntu:14.04
MAINTAINER milaw <gmilaw@gmail.com>

# Update
RUN apt-get update
RUN apt-get -y upgrade

# Install pip
RUN apt-get -y install python-pip

RUN apt-get -y install python-dev liblzma-dev libevent1-dev gcc python-dev

RUN pip install blist \
	lz4 \
	cassandra-driver

# Install docker-registry
RUN pip install docker-registry docker-registry-driver-cassandra

ADD . /docker-registry-driver-cassandra

ENV DOCKER_REGISTRY_CONFIG /docker-registry-driver-cassandra/config/config.yml
ENV SETTINGS_FLAVOR cassandra

EXPOSE 5000
