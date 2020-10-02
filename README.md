# Simple Goniometer Interface (SGI)

## The idea
**TODO** Provide a universal interface for Goniometer device that allows synchronized video / image capture.
### Setup
**TODO** Customized MCA-3
### Workflow
**TODO** *Draw the scheme of the interface*?

## Installation
### Control computer part
**TODO** 
- Python + Qt part
- Correctly setting the rc files?
### Camera side
**TODO** 
- On-computer camera?
- On-chip / RPi camera?
- ssh setup
- ssh call-up
#### Simple determination of video output 
1. Install the video4linux2 (v4l2) utilities, i.e. via `sudo apt-get install v4l2-utils`
2. Check which video device is recognized by running `v4l2-ctl --list-devices`
3. Figure out the channel number for the input e.g. composite using
   `v4l2-ctl -n -d /dev/video0`. 
4. Check if video capture is working using utilities like `qv4l2` or `yavta`

#### Installation on the Linux/RasPi/VM part
1. Enable the ssh server on Linux machine. `sudo apt-get update; sudo apt-get install openssh-server`. 
2. If the `sshd` service is down, strat it by `sudo service sshd start`
3. Make sure ssh into the VM is possible. Likely the bridged network is necessary.
4. Install the requirements: `sudo apt-get install git curl python3 python3-pip python3-venv motion`
5. Disable the default motion service 
