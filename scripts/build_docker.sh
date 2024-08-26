#!/bin/bash
docker build -t log_summarizer-log_analyzer:latest --build-arg UID=$(id -u) .
