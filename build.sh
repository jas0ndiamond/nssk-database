#!/bin/bash

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: ./build.sh config.json"
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing config file $CONFIG_FILE. Create this file from the template."
  exit 1
fi

##################################
# check if we have jq
which jq > /dev/null
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Could not find jq on PATH. Please install jq. Exiting..."
  exit 1
fi

##################################
# get the image name
IMAGE_NAME="$(jq -r '."image_name"' < "$CONFIG_FILE")"
if [ -z "$IMAGE_NAME" ]; then
  echo "image_name not readable from config"
  exit 1
fi

##################################
# file resource checks - viable files created outright, from templates, or from the generation process
# fail2ban/fail2ban.conf
F2B_CONF_FILE="$PROJECT_ROOT/fail2ban/fail2ban.conf"
F2B_JAIL_FILE="$PROJECT_ROOT/fail2ban/jail.local"
if [ ! -f "$F2B_CONF_FILE" ]; then
  echo "Missing fail2ban conf file $F2B_CONF_FILE"
  exit 1
fi

# fail2ban/jail.local
if [ ! -f "$F2B_JAIL_FILE" ]; then
  echo "Missing fail2ban jail file $F2B_JAIL_FILE"
  exit 1
fi

# conf.d/
DB_CONFD_DIR="$PROJECT_ROOT/mysql/conf.d"
if [ ! -d "$DB_CONFD_DIR" ]; then
  echo "Missing database custom confd directory $DB_CONFD_DIR"
  exit 1
fi

# conf.d/nssk.cnf
NSSK_DB_CUSTOM_CONF_FILE="$DB_CONFD_DIR/nssk.cnf"
if [ ! -f "$NSSK_DB_CUSTOM_CONF_FILE" ]; then
  echo "Missing mysql confd file $NSSK_DB_CUSTOM_CONF_FILE"
  exit 1
fi

# conf.d/nssk-ext.cnf
NSSK_DB_CUSTOM_CONF_EXT_FILE="$DB_CONFD_DIR/nssk-ext.cnf"
if [ ! -f "$NSSK_DB_CUSTOM_CONF_EXT_FILE" ]; then
  echo "Missing mysql extended confd file $NSSK_DB_CUSTOM_CONF_EXT_FILE"
  exit 1
fi

# logrotate.d
LOGROTATE_CONF_DIR="$PROJECT_ROOT/logrotate.d"
if [ ! -d "$LOGROTATE_CONF_DIR" ]; then
  echo "Missing logrotate.d config directory $LOGROTATE_CONF_DIR"
  exit 1
fi

# logrotate.d/mysqld-nssk
NSSK_DB_LOGROTATE_CONF_FILE="$LOGROTATE_CONF_DIR/mysqld-nssk"
if [ ! -f "$NSSK_DB_LOGROTATE_CONF_FILE" ]; then
  echo "Missing logrotate conf file $NSSK_DB_LOGROTATE_CONF_FILE"
  exit 1
fi

# check database_setup directory. can't build image without these resources
DB_SETUP_SCRIPT_DIR="$PROJECT_ROOT/database_setup"
if [ ! -d "$DB_SETUP_SCRIPT_DIR" ]; then
  echo "Missing database setup scripts directory $DB_SETUP_SCRIPT_DIR. Make sure generate_db_setup.py has been executed."
  exit 1
fi

##################################
# build image
echo "Building image $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" .
