#!/bin/bash
docker build -t log_analyzer:latest --build-arg UID=$(id -u) .
