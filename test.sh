#!/bin/bash

docker build -t hist .
docker build -t repo ../repo

docker run --name analysis-master -v /var/run/docker.sock:/var/run/docker.sock hist python main.py $@

DATE=`date +%Y-%m-%d-%H-%M-%S`

docker cp analysis-master:/app/output.csv $DATE.csv

docker rm analysis-master