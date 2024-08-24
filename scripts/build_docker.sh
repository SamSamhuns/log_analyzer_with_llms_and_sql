#!/bin/bash
docker build -t log_summarizer-log_analyze:latest --build-arg UID=$(id -u) .
