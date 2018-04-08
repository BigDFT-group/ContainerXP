#! /bin/sh
# Usage: $0 sourcedir containerdir 

dirname="$(basename $PWD)"
xhost +local:root #requires x11-xserver-utils
docker run -ti  \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $1:/bigdft-suite-sources/ \
    -v $2:/bigdft-sdk/ \
    -v $PWD:/$dirname -w /$dirname \
    bigdft/sdk:cuda9-ompi bash
