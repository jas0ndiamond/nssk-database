#!/bin/bash

# typically this is done manually but this script attempts to streamline stuff
# requires dump to be created with backup.sh script
# will attempt to create databases and tables if they don't exist

CONF_FILE=$1
DB_DUMP_FILE=$2

##################################
# check if we have jq
which jq > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find jq on PATH. Please install jq. Exiting..."
  exit 1
fi

##################################
# check if we have mysql.
# backups and restores can be run remotely so it's not ridiculous that this wouldn't be on a non-database host
# plus it's quick to check.

which mysql > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find mysql on PATH. Please install mysql. Exiting..."
  exit 1
fi

##################################
# read credentials for our restore user

if [ -z "$CONF_FILE" ]; then
  echo "Need config file"
  exit 1
fi

if [ ! -f "$CONF_FILE" ]; then
  echo "Config file does not exist"
  exit 1
fi

# hardcode for now
USER="nssk_admin"

# read from config
HOST="$(jq -r '.network.listen_ip' < "$CONF_FILE")"
PORT="$(jq -r '.network.listen_port' < "$CONF_FILE")"
PASS="$(jq -r '.users.internal.nssk_admin' < "$CONF_FILE")"

if [[ -z $HOST ]]; then
  echo "Could not read host"
  exit 1
fi

if [[ -z $PORT ]]; then
  echo "Could not read port"
  exit 1
fi

if [[ -z $USER ]]; then
  echo "Could not read user"
  exit 1
fi

if [[ -z $PASS ]]; then
  echo "Could not read password"
  exit 1
fi

##################################
# check we have a valid dump file

if [ -z "$DB_DUMP_FILE" ]; then
  echo "Need database dump file"
  exit 1
fi

if [ ! -f "$DB_DUMP_FILE" ]; then
  echo "Database dump file does not exist"
  exit 1
fi

# ends in .sql
if [[ "$DB_DUMP_FILE" =~ \.[sS][qQ][lL]$ ]]; then
  echo "Database dump file extension check passed"

  # dump file preamble check
  # first lines (preamble) of dump file matches "-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB, "
  if head -n 6 "$DB_DUMP_FILE" | grep -qE -- '^-- MariaDB dump [0-9]{1,5}\.[0-9]{1,5}  Distrib [0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}-MariaDB,'; then
      echo "Database dump file preamble check passed"
  else
      echo "Database dump file preamble check failed. Dump file preamble must contain '-- MariaDB dump '"
      exit 1
  fi

  # command for restoring from an uncompressed file (.sql)
  CMD="mysql -h $HOST -P $PORT -u $USER --password='$PASS' -f < $DB_DUMP_FILE"
elif [[ "$DB_DUMP_FILE" =~ \.[sS][qQ][lL]\.gz$ ]]; then
  echo "Database compressed dump file extension check passed"

  # TODO: more checks on compressed dump file?

  # command for restoring from an compressed file (.sql.gz)
  CMD="gunzip < $DB_DUMP_FILE | mysql -h $HOST -P $PORT -u $USER --password=\"$PASS\" -f"
else
  echo "Database dump file has unexpected extension. Extension must end with '.sql' or '.sql.gz'"
  exit 1
fi

# would it be easy to check that all tables are empty? maybe but just throw this in the warning

####################

# final prompt before running restore

# WARNING prompt to confirm a fresh database instance is at host/port, and is ready
# warn about restoring to a hot db

echo "============================================================"
echo "WARNING: You are attempting a database restore."
echo -e "\tDatabase Dump File: $DB_DUMP_FILE"
echo -e "\tDatabase: $HOST:$PORT"
echo -e "\tUser: $USER"
echo "This is often a destructive operation, and may result in data loss."
echo "Ensure that the NSSK database instance is empty and ready for restore."
echo "============================================================"
read -r -p "Proceed? (Y/N): " confirm && ( [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || { echo "Did not get confirmation. Bailing..."; exit 1; } )

# debug
#echo "Command $CMD"

eval "$CMD"
