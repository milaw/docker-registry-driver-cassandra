# Latest Ubuntu LTS
FROM registry
MAINTAINER milaw <gmilaw@gmail.com>

# Update
RUN apt-get update
RUN apt-get -y upgrade

# Install pip
RUN apt-get -y install swig python-pip

RUN apt-get -y install python-dev liblzma-dev libevent1-dev gcc python-dev

# Install library
RUN pip install blist lz4 
# Install python client
RUN	pip install cassandra-driver
# Install driver
COPY . /src
RUN pip install /src

#RUN pip install docker-registry-driver-cassandra

ADD . /docker-registry-driver-cassandra
#ADD docker_registry/drivers docker-registry/docker_registry/drivers
#ENV DOCKER_REGISTRY_CONFIG /docker-registry-driver-cassandra/config/config.yml
#ENV SETTINGS_FLAVOR cassandra
