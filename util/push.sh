#!/bin/bash

# deploy database to container server

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")/.."

USER=$1
HOST=$2
PATH=$3

if [ -z "$USER" ]; then
  echo "User required"
  exit 1;
fi

if [ -z "$HOST" ]; then
  echo "Host required"
  exit 1;
fi

if [ -z "$PATH" ]; then
  echo "Path required. (/home/user/)"
  exit 1;
fi

PATH="$(dirname $PATH)"

TARGET="$USER@$HOST:$PATH"


CMD="/usr/bin/rsync --exclude=$PROJECT_ROOT/data --exclude=$PROJECT_ROOT/mysql -ruvh $PROJECT_ROOT $TARGET"

echo $CMD

eval $CMD
