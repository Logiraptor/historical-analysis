#!/bin/bash

docker build -t hist .

docker run -v $(pwd):/app -v /var/run/docker.sock:/var/run/docker.sock -it -p 8888:8888 hist jupyter notebook --allow-root --ip 0.0.0.0