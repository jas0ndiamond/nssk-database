#!/bin/bash

# push this repo to a remote server via rsync (this does not push a docker image to
# a registry, despite the name)

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"

if [ "$1" == "-h" ] || [ "$1" == "-help" ] || [ "$1" == "--help" ]; then
  echo "Usage: ./push.sh user host path"
  echo "  Rsyncs this repo to user@host:path (excludes ./data and ./mysql)."
  echo "  Does not push a docker image to a registry, despite the name."
  exit 0
fi

RSYNC_USER=$1
RSYNC_HOST=$2
REMOTE_PATH=$3

if [ -z "$RSYNC_USER" ]; then
  echo "User required"
  exit 1
fi

if [ -z "$RSYNC_HOST" ]; then
  echo "Host required"
  exit 1
fi

if [ -z "$REMOTE_PATH" ]; then
  echo "Path required. (/home/user/)"
  exit 1
fi

REMOTE_PATH="$(dirname "$REMOTE_PATH")"

TARGET="$RSYNC_USER@$RSYNC_HOST:$REMOTE_PATH"

echo "/usr/bin/rsync --exclude=$PROJECT_ROOT/data --exclude=$PROJECT_ROOT/mysql -ruvh $PROJECT_ROOT $TARGET"

/usr/bin/rsync --exclude="$PROJECT_ROOT/data" --exclude="$PROJECT_ROOT/mysql" -ruvh "$PROJECT_ROOT" "$TARGET"
