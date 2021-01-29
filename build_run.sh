#!/bin/bash
app="go-cookbook"
docker build -t ${app} .

if [ $# -ne 1 ]; then
  docker run -d -p 5001:5001 \
  --name=${app} \
  -v "$PWD:/app" ${app}

fi


if [ "$1" == "-prod" ]; then
  docker run \
  -d -p 5001:5001 \
  --name=${app} \
  -v "$PWD:/app" ${app} \
  gunicorn -w 2 -b 0.0.0.0:5001 manage:app
  
fi