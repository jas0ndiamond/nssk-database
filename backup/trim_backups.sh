#!/bin/bash

# run a database backup of a nssk database instance
# system dump is not performed for now
# expectation is backup is restored into a fresh instance
# deletes .sql and .sql.* backups

MAX_DEL=20
MIN_KEEP=20

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Need backup directory"
  exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory does not exist"
  exit 1
fi

# naming
# nssk_database_backup_2025-03-29_230328.sql.gz
# nssk_database_backup_2025-03-29_230340.sql.gz
#...

# trim backups if we're over our maximum
BACKUP_COUNT=$(/bin/ls -l "$BACKUP_DIR" | grep -cv "^total")
if [ "$BACKUP_COUNT" -gt $MIN_KEEP ]; then
        /bin/ls -l "$BACKUP_DIR" | grep "nssk_database_backup_.*\.sql*" | head -$MAX_DEL | awk -v mydir="$BACKUP_DIR" '{print mydir"/"$NF}' | xargs rm -v
else
        echo "Skipping backup trim for backup count $BACKUP_COUNT in directory $BACKUP_DIR"
fi
