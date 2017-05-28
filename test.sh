#!/bin/bash

docker build -t hist .
docker build -t repo ../repo

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock hist python main.py $@
