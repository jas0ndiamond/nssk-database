#!/bin/bash

if [[ -z $1 || -z $2 ]]; then
  echo "Run a backup of the database with a config file and destination for the backup."
  echo "Usage: backup.sh confFile backupDirectory"
  exit 1
fi

CONF_FILE=$1
BACKUP_DIR=$2

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
# check if we have mysql (used to discover the database list to back up)

which mysql > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find mysql on PATH. Please install mysql. Exiting..."
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

if [ -z "$CONF_FILE" ]; then
  echo "Need config file"
  exit 1
fi

if [ ! -f "$CONF_FILE" ]; then
  echo "Config file does not exist"
  exit 1
fi

USER="nssk_backup"
HOST="$(jq -r '.network.listen_ip' < "$CONF_FILE")"
PORT="$(jq -r '.network.listen_port' < "$CONF_FILE")"
PASS="$(jq -r '.users.internal.nssk_backup' < "$CONF_FILE")"

if [[ -z $HOST ]]; then
  echo "Could not read host"
  exit 1
fi

if [[ -z $PORT ]]; then
  echo "Could not read port"
  exit 1
fi

if [[ -z $PASS ]]; then
  echo "Could not read password"
  exit 1
fi

# short-lived credentials file so the password never appears on the mysqldump command
# line (and thus never shows up in `ps` output). Removed on exit regardless of outcome.
CRED_FILE="$(mktemp)"
trap 'rm -f "$CRED_FILE"' EXIT
chmod 600 "$CRED_FILE"
{
  echo "[client]"
  echo "user=$USER"
  echo "password=$PASS"
} > "$CRED_FILE"

TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
DUMP_FILE=$BACKUP_DIR/nssk_database_backup_"$TIMESTAMP".sql

# Discovered, not hardcoded, so this doesn't drift from the actual database list
# in src/generate_db_setup.py as datasets are added/removed. Deliberately NOT
# --all-databases: that would include the mysql system schema, and nssk_backup
# has no privileges there anyway. It wouldn't help even if granted - MySQL 8's
# mysql.* tables live in a reserved tablespace and cannot be recreated via a
# plain CREATE TABLE/mysqldump replay, so that data could never actually be
# restored (verified: a restore attempt fails with "may not be created in the
# reserved tablespace 'mysql'" regardless of the restoring user's privileges).
DB_LIST="$(mysql --defaults-extra-file="$CRED_FILE" -h "$HOST" -P "$PORT" -N -e "SHOW DATABASES;" | grep -vE '^(information_schema|performance_schema|mysql|sys)$')"

if [[ -z "$DB_LIST" ]]; then
  echo "Could not determine database list to back up"
  exit 1
fi

echo "Dumping NSSK database tables to $DUMP_FILE"
# shellcheck disable=SC2086
mysqldump\
 --defaults-extra-file="$CRED_FILE"\
 -P "$PORT"\
 -h "$HOST"\
 --databases $DB_LIST > "$DUMP_FILE"

result=$?
if [ $result -eq 0 ]; then
  echo "Backup successful"

  # backups can be in the gigabyte range. gzip compresses this a lot. other compression tools would work fine too
  # gzip by default does not keep the original file. so no need to manually delete.
  echo -n "Compressing backup..."
  gzip "$DUMP_FILE"
  echo "Done"
else
  echo "Backup failed"
  exit 1
fi

exit 0
