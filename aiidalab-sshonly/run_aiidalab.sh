#!/bin/bash

if [[ $# -ne 2 ]] && [[ $# -ne 3 ]]
  then
    echo "Please provide 2 or 3 arguments: free port of your computer, a folder to mount as aiida's home, and an optional key to use as password for jupyter (if absent, one is generated)"
    echo "If the folder does not exit, it will be created automatically."
    echo ''
    echo 'Example:'
    echo '$ ./run_aiidalab.sh 8888 ${HOME}/aiidalab'
    exit 1
fi

PORT=${1}
FOLDER=${2}
if [ -z $3 ]
then
  TOKEN=`openssl rand -hex 32`
else
  TOKEN=$3
fi

IMAGE='bigdft/aiidalab-docker:latest'
echo "Pulling the image from the Docker Hub..."
docker pull ${IMAGE}

echo "Launching the container..."
CONTAINERID=`docker run -d -p ${PORT}:8888 -e JUPYTER_TOKEN=${TOKEN} -v "${FOLDER}":/home/aiida ${IMAGE}`

echo "Waiting for container to start..."
docker exec --tty ${CONTAINERID} wait-for-services

echo "Container started successfully."
echo "Open this link in the browser to enter AiiDA lab:"
echo "http://localhost:${PORT}/?token=${TOKEN}"
