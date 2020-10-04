#!/bin/bash
function vercomp {
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}

function check_motion {
    # Check if the motion binary and versions are correct
    motion_bin=$(which motion)
    if ! [[ $? == 0 ]]; then
        return -1
    fi
    local version_motion=$(motion -h | grep -Po "Version\s+(\K\d.\d.\d)")
    vercomp ${version_motion} "4.2.0"
    if [[ $? == 2 ]]; then
	return 1
    fi
    return 0
    # Return:
    # 0: Success, can use the ${motion_bin}
    # 1: motion version too low
    # -1: motion binary not found
}

function check_motion_pid {
    # Check if the pid of motion runs
    # Can exist multiple motion procees!
    motion_pid=$(pgrep motion)
    if [[ -z ${motion_pid} ]]; then
	return 1
    fi
}

function kill_motion_proc {
    local pids=$@
    #for pid in $pids; do
    kill -9 $pids
    #done
    sleep 2 # Wait until kill finish
    return $?
}

function main {
    MOTION_ROOT=${HOME}/SGI/motion
    if [[ -z "${MOTION_CONF_FILE}" ]]; then
	MOTION_CONF_FILE=${MOTION_ROOT}/motion.conf
    fi
    if [[ -z "${MOTION_PID_FILE}" ]]; then
	MOTION_PID_FILE=${MOTION_ROOT}/proc.pid
    fi
    if [[ -z "${MOTION_LOG_FILE}" ]]; then
	MOTION_LOG_FILE=${MOTION_ROOT}/motion.log
    fi

    # Check file existence
    mkdir -p ${MOTION_ROOT}
    if ! [[ -f ${MOTION_CONF_FILE} ]]; then
	>&2 echo "Warning! Motion config file ${MOTION_CONF_FILE} not found!"
    fi
    
    
    # Check motion
    check_motion
    local code=$?
    if [[ $code != 0 ]]; then
	local ERROR_MSG
	if [[ $code == -1 ]]; then
	    ERROR_MSG="No motion binary found!"
	elif [[ $code == 1 ]]; then
	    ERROR_MSG="Motion version should be higher than 4.2.0!"
	fi
	# output error message
	>&2 echo ${ERROR_MSG}
    fi
    # motion_bin should be usable now
    check_motion_pid
    local clear=${#motion_pid}
    while [[ $clear > 0 ]];do
	# If return 0 means motion is running
	# echo ${motion_pid} $clear
	if [[ $? == 0 ]]; then
	    echo "I'm going to kill the following running motion processes"
	    echo ${motion_pid}
	    kill_motion_proc ${motion_pid}
	fi
	check_motion_pid
	clear=${#motion_pid}
    done
    # Finally trying to run motion!
    echo "Trying to start motion process......"
    ${motion_bin} \
	  -l ${MOTION_LOG_FILE} \
	  -c ${MOTION_CONF_FILE} \
      	  -p ${MOTION_PID_FILE} -b -m
    check_motion_pid
    echo "Running motion on process ${motion_pid}"
}

main

