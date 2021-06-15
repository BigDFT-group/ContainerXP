#!/bin/sh
ORIGIN=$(dirname $(readlink -f $0))
. "$ORIGIN/uniopt.sh"

uniopt WITH_DISPLAY X display ASSUME_NO "Enable host display usage (requires x11-xserver-utils)"
uniopt SOURCEDIR s sources "\${HOME}/bigdft-suite" "Source directory (provide absolute path)"
uniopt CONTAINER i image "bigdft/sdk" "SDK Container image to deploy"
uniopt BINARIES b binaries "\${HOME}/binaries" "Binaries directory (provide absolute path)"
uniopt WITH_WORKDIR w workdir ASSUME_NO "Include present directory in the container"
uniopt EMPLOY_ROOT_USER r root ASSUME_NO "Employ present user in the container"
uniopt EXTRA_COMMANDS c extra-cmd "" "Extra commands to be provided to docker WARNING: Spaces are not tolerated, use long commands"
uniopt HOMEDIR h homedir "/tmp/fake_home" "Directory of homedir of the container. Useful eg. to preserve history."
uniopt PORT p port '8888' "Port to which redirect the 8888 port of the container"

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
	    mkdir -p $HOMEDIR
	    REHOME=$(get_abspath $HOMEDIR)
            DOCKER_OPTIONS="$DOCKER_OPTIONS -u $local_user -v /etc/passwd:/etc/passwd:ro -v $REHOME:/home/$USER -v $HOME/.ssh:/home/$USER/.ssh"
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
DOCKER_OPTIONS="$DOCKER_OPTIONS -v $SRC:/opt/bigdft/sources/ -v $BIN:/opt/bigdft/ --hostname $CONTAINER -p $PORT:8888 $EXTRA_COMMANDS"
DOCKER_COMMAND="docker run -ti $DOCKER_OPTIONS $CONTAINER $POSITIONAL"
echo "$DOCKER_COMMAND"

