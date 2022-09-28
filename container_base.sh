#!/bin/sh
ORIGIN=$(dirname $(readlink -f $0))
. "$ORIGIN/uniopt.sh"

uniopt WITH_DISPLAY X display ASSUME_NO "Enable host display usage (requires x11-xserver-utils)"
uniopt WITH_WORKDIR w workdir ASSUME_NO "Include present directory in the container"
uniopt EMPLOY_ROOT_USER r root ASSUME_NO "Employ present user in the container"
uniopt EXTRA_COMMANDS x extra-cmd "" "Extra commands to be provided to docker WARNING: Spaces are not tolerated, use long commands"
uniopt HOMEDIR d homedir "/tmp/fake_home" "Directory of homedir of the container. Useful eg. to preserve history."

enable_display() {
if test "$WITH_DISPLAY" = "YES"; then
    xhost +local:root > /dev/null
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
	    local_group=$(id -g)
	    user_name=$(id -un)
	    group_name=$(id -gn)
	    mkdir -p $HOMEDIR
	    REHOME=$(get_abspath $HOMEDIR)
	    NEWHOME=$HOME
	    cp /etc/passwd $HOMEDIR
	    user_search=$(grep ":x:$local_user:" $HOMEDIR/passwd)
	    if test x"$user_search" = x; then
		    echo $user_name:x:$local_user:$local_group:$user_name,,,:$NEWHOME:/bin/bash >> $HOMEDIR/passwd
	    fi
	    cp /etc/group $HOMEDIR
	    group_search=$(grep ":x:$local_group:" $HOMEDIR/passwd)
	    if test x"$group_search" = x; then
		    echo $group_name:x:$local_group:$user_name >> $HOMEDIR/group 
	    fi
    
            DOCKER_OPTIONS="$DOCKER_OPTIONS -u $local_user:$local_group -v $REHOME/passwd:/etc/passwd:ro -v $REHOME/group:/etc/group:ro -v $REHOME:$NEWHOME -v $HOME/.ssh:$NEWHOME/.ssh:ro -v $HOME/.gitconfig:$NEWHOME/.gitconfig:ro "
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

parse_base(){
    uniopt_parser $@

    DOCKER_OPTIONS=""

    enable_display
    enable_workdir
    enable_current_user
    DOCKER_OPTIONS="$DOCKER_OPTIONS --hostname $CONTAINER $EXTRA_COMMANDS"
}

docker_command() {
    DOCKER_COMMAND="docker run -ti $DOCKER_OPTIONS $CONTAINER $POSITIONAL"
    echo "$DOCKER_COMMAND"
}

