# Latest Ubuntu LTS
FROM registry
MAINTAINER milaw <gmilaw@gmail.com>

# Update
# Install pip
# Install library
# Install python client
RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get -y install swig python-pip && \
	apt-get -y install python-dev liblzma-dev libevent1-dev gcc python-dev && \
	pip install blist lz4 && \
	pip install cassandra-driver

# Install driver
COPY . /src
RUN pip install /src

#RUN pip install docker-registry-driver-cassandra

ADD . /docker-registry-driver-cassandra
ADD docker_registry/drivers docker-registry/docker_registry/drivers
#ENV DOCKER_REGISTRY_CONFIG /docker-registry-driver-cassandra/config/config.yml
#ENV SETTINGS_FLAVOR cassandra
