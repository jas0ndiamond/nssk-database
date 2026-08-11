#!/bin/bash

# destructively remove and re-create the nssk-database container.
# purges ./mysql/data and ./mysql/log, so the next start is a fresh instance.

if [ "$1" == "-h" ] || [ "$1" == "-help" ] || [ "$1" == "--help" ]; then
  echo "Usage: ./redeploy.sh config.json"
  echo "  DESTRUCTIVE: docker compose down, purges ./mysql/data and ./mysql/log,"
  echo "  then runs ./deploy.sh for a fresh instance. All database state is lost."
  exit 0
fi

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: ./redeploy.sh config.json"
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing config file '$CONFIG_FILE'. Create this file from the template."
  exit 1
fi

docker compose down

# purge database state
sudo rm -rf "./mysql/data"
sudo rm -rf "./mysql/log"

# run regular deploy
./deploy.sh "$CONFIG_FILE"
