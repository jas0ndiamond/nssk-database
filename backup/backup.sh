#!/bin/bash

BACKUP_DIR=$1
CRED_FILE=$2

##################################
# check if we have jq
which jq > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find jq on PATH. Please install jq. Exiting..."
  exit 1
fi

##################################
# check if we have gzip
which gzip > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find gzip on PATH. Please install gzip. Exiting..."
  exit 1
fi

##################################
# check if we have mysqldump. backups can be run remotely so it's not ridiculous, and it's quick to check.

which mysqldump > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find mysqldump on PATH. Please install mysqldump. Exiting..."
  exit 1
fi

##################################
# parameter check

if [ -z "$BACKUP_DIR" ]; then
  echo "Need backup directory"
  exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory does not exist"
  exit 1
fi

if [ -z "$CRED_FILE" ]; then
  echo "Need credential file"
  exit 1
fi

if [ ! -f "$CRED_FILE" ]; then
  echo "Credential file does not exist"
  exit 1
fi

USER="nssk_backup"
HOST="$(jq -r '.network.listen_ip' < "$CRED_FILE")"
PORT="$(jq -r '.network.listen_port' < "$CRED_FILE")"
CRED="$(jq -r '.users.nssk_backup' < "$CRED_FILE")"

if [[ -z $HOST ]]; then
  echo "Could not read host"
  exit 1
fi

if [[ -z $PORT ]]; then
  echo "Could not read port"
  exit 1
fi

if [[ -z $CRED ]]; then
  echo "Could not read credentials"
  exit 1
fi

# create directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
  mkdir -p "$BACKUP_DIR"

  if [ ! -d "$BACKUP_DIR" ]; then
    echo "Failed to create backup directory. Exiting"
    exit 1
  fi
fi

TIMESTAMP=$(date +"%Y-%m-%d_%H%m%S")
DUMP_FILE=$BACKUP_DIR/nssk_database_backup_"$TIMESTAMP".sql
#DUMP_SYSTEM_FILE=$BACKUP_DIR/nssk_dump_system_"$TIMESTAMP".sql

echo "Dumping NSSK database tables to $DUMP_FILE"
mysqldump\
 -u $USER\
 -P "$PORT"\
 -h "$HOST"\
 --password="$CRED"\
 --all-databases > "$DUMP_FILE"

# backups can be in the gigabyte range. gzip compresses this a lot. other compression tools would work fine too
# gzip by default does not keep the original file. so no need to manually delete.
echo -n "Compressing backup..."
gzip "$DUMP_FILE"
echo "Done"

# TODO: sort out permissions and retry
#echo "Dumping database system state to $DUMP_SYSTEM_FILE"
#mysqldump\
# -u $USER\
# -P "$PORT"\
# -h $HOST\
# --password="$CRED"\
# --system=all > "$DUMP_SYSTEM_FILE"

