#! /bin/sh
# Usage: $0 prefixdir 

dirname="$(basename $PWD)"
xhost +local:root #requires x11-xserver-utils
docker run -ti  \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $2:/bigdft \
    -v $PWD:/$dirname -w /$dirname \
    bigdft/sdk:cuda9-ompi
