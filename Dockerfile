
FROM ubuntu

ENV DOCKER_VERSION 17.03.0-ce

RUN apt-get update && apt-get install -y curl

RUN curl -fsSLO https://get.docker.com/builds/Linux/x86_64/docker-${DOCKER_VERSION}.tgz \
    && tar --strip-components=1 -xvzf docker-${DOCKER_VERSION}.tgz -C /usr/local/bin

RUN apt-get install -y python-pip

RUN pip install docker

ADD . /app
WORKDIR /app
