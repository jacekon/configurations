#!/usr/bin/env bash
docker run --net=host --ipc host -u $(id -u):$(id -g) -v /etc/passwd:/etc/passwd:ro -v /home/jacek:/home/jacek -e DISPLAY=:1 --privileged=true -ti --rm orcaslicer

