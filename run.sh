#!/bin/sh
ORIGIN=$(dirname $(readlink -f $0))
. "$ORIGIN/uniopt.sh"

uniopt WITH_DISPLAY X display ASSUME_NO "Enable host display usage (requires x11-xserver-utils)"
uniopt SOURCEDIR s sources "\${HOME}/bigdft-suite" "Source directory (provide absolute path)"
uniopt CONTAINER i image "bigdft/sdk" "SDK Container image to deploy"
uniopt BINARIES b binaries "\${HOME}/binaries" "Binaries directory (provide absolute path)"
uniopt WITH_WORKDIR w workdir ASSUME_NO "Include present directory in the container"
uniopt EMPLOY_ROOT_USER r root ASSUME_NO "Employ present user in the container"

uniopt_parser $@

DOCKER_OPTIONS=""

enable_display() {
if test "$WITH_DISPLAY" = "YES"; then
    xhost +local:root
    DOCKER_OPTIONS="$DOCKER_OPTIONS -e DISPLAY=\$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix"
fi
}

enable_workdir()
{
    if test "$WITH_WORKDIR" = "YES"; then
	    dirname="$(basename $PWD)"
            DOCKER_OPTIONS="$DOCKER_OPTIONS -v $PWD:/$dirname -w /$dirname"
    fi
}

enable_current_user()
{
    if test "$EMPLOY_ROOT_USER" = "NO"; then
            dirname="$(basename $PWD)"
	    local_user=$(id -u)
            DOCKER_OPTIONS="$DOCKER_OPTIONS -u $local_user -v /etc/passwd:/etc/passwd:ro -v $HOME:/home/$USER:ro"
    fi
}


get_abspath(){
    if test -d "$1"; then
        cd "$1"
        echo "$(pwd -P)"
    else
        cd "$(dirname "$1")"
        echo "$(pwd -P)/$(basename "$1")"
    fi
}


enable_display
enable_workdir
enable_current_user
SRC=$(get_abspath $SOURCEDIR)
BIN=$(get_abspath $BINARIES)
DOCKER_OPTIONS="$DOCKER_OPTIONS -v $SRC:/opt/bigdft/sources/ -v $BIN:/opt/bigdft/"
DOCKER_COMMAND="docker run -ti $DOCKER_OPTIONS $CONTAINER $POSITIONAL"
echo "$DOCKER_COMMAND"
#docker run -ti  \
#    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
#    -v $1:/bigdft-suite-sources/ \
#    -v $2:/bigdft-sdk/ \
#    -v $PWD:/$dirname -w /$dirname \
#    bigdft/sdk:cuda9-ompi bash

