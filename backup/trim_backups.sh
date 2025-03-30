#!/bin/bash

MAX_DEL=20
MIN_KEEP=20

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Need backup directory"
  exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory does not exist"
  exit 1
fi

#nssk_dump_2024-03-17_000301.sql
#nssk_dump_2024-05-04_000501.sql
#...

#nssk_dump_system_2024-04-10_000401.sql
#nssk_dump_system_2024-04-11_000401.sql
#...



# trim backups if we're over our maximum
BACKUP_COUNT=$(/bin/ls -l "$BACKUP_DIR" | grep -cv "^total")
if [ "$BACKUP_COUNT" -gt $MIN_KEEP ]; then
        /bin/ls -l "$BACKUP_DIR" | grep "nssk_data_dump_.*\.xml$" | head -$MAX_DEL | awk -v mydir="$BACKUP_DIR" '{print mydir"/"$NF}' | xargs rm -v
else
        echo "Skipping backup trim for backup count $BACKUP_COUNT in directory $BACKUP_DIR"
fi

exit 0;

