#!/bin/bash
docker build -t log_summarizer:latest --build-arg UID=$(id -u) .
