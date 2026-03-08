#! /bin/sh
# Usage: put the command arguments in the line 
dirname="$(basename $PWD)"
xhost +local:root #requires x11-xserver-utils
docker run -ti  \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $PWD:/$dirname -w /$dirname \
    lsimlab/v_sim-dev:16.04 bash
