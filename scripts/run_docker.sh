#!/bin/bash

def_cont_name=log_summarizer-log_analyze_cont

helpFunction()
{
   echo ""
   echo "Usage: $0 -p port"
   echo -e "\t-p http_port"
   exit 1 # Exit script after printing help
}

while getopts "p:" opt
do
   case "$opt" in
      p ) port="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$port" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

# Check if the container is running
if [ "$(docker ps -q -f name=$def_cont_name)" ]; then
    echo "Stopping docker container '$def_cont_name'"
    docker stop "$def_cont_name"
    docker rm "$def_cont_name"
    echo "Stopped container '$def_cont_name'"
fi

mkdir -p "$PWD/volumes/log_analyzer"  # create shared vol with correct perms
docker run \
      -ti --rm -d \
      -p "0.0.0.0:$port:8080" \
      -v "$PWD/volumes/log_analyzer:/home/user1/log_analyzer/data" \
      --name "$def_cont_name" \
      log_summarizer-log_analyze:latest
