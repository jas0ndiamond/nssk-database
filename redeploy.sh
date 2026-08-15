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

# purge database state - uses a throwaway container (root in its own namespace)
# instead of sudo: ./mysql/data is owned by the in-container mysql uid, which the
# host user can't delete directly, and this avoids needing host-level sudo access
# at all - consistent with the rest of this script, which only ever uses docker.
# mysql:8.0-debian (this project's own base image, not a new image to pull) rather
# than a generic minimal image: it's guaranteed to be pullable/present even on a
# fresh checkout where nothing has been deployed yet - unlike this project's own
# built nssk-mysql image, which only exists locally after a build has happened,
# and isn't published anywhere to fall back to pulling if it doesn't.
docker run --rm -v "$(pwd)/mysql":/purge mysql:8.0-debian sh -c "rm -rf /purge/data /purge/log"

# run regular deploy
./deploy.sh "$CONFIG_FILE"
