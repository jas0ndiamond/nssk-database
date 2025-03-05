#!/bin/bash

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: ./build.sh config.json"
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing config file $CONFIG_FILE. Create this file from the template."
  exit 1
fi

##################################
# check if we have jq
which jq > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find jq on PATH. Please install jq. Exiting..."
  exit 1
fi

##################################
# get the image name
IMAGE_NAME="$(jq -r '."image_name"' < "$CONFIG_FILE")"
if [ -z "$IMAGE_NAME" ]; then
  echo "image_name not readable from config"
  exit 1
fi

##################################
# build image
docker build -t "$IMAGE_NAME" .
