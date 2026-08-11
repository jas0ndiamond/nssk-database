#!/bin/bash

# destructively remove and re-create the nssk-database container.
# purges ./mysql/data and ./mysql/log, so the next start is a fresh instance.

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
