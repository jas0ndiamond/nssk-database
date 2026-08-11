#!/bin/bash

# generate config from the given config file, then build and (re)start the
# container via docker compose. Non-destructive - leaves ./mysql/data and
# ./mysql/log alone.

if [ "$1" == "-h" ] || [ "$1" == "-help" ] || [ "$1" == "--help" ]; then
  echo "Usage: ./deploy.sh config.json"
  echo "  Runs ./generate-config.sh, then docker compose up -d --build."
  echo "  Non-destructive - leaves ./mysql/data and ./mysql/log alone."
  exit 0
fi

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
  echo "Usage: ./deploy.sh config.json"
  exit 1
fi

./generate-config.sh "$CONFIG_FILE" && docker compose up -d --build
