#!/bin/bash

# run from same directory

# TODO: re-enable?
# can be problematic if database is misconfigured
# --restart=unless-stopped\

########################

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: ./start.sh config.json"
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing config file '$CONFIG_FILE'. Create this file from the template."
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

# conf.d/nssk.cnf
# require this as it enables logging for fail2ban
DB_CONFD_DIR="$PROJECT_ROOT/mysql/conf.d"
if [ ! -d "$DB_CONFD_DIR" ]; then
  echo "Missing database custom confd directory $DB_CONFD_DIR"
  exit 1
fi

NSSK_DB_CUSTOM_CONF_FILE="$DB_CONFD_DIR/nssk.cnf"
if [ ! -f "$NSSK_DB_CUSTOM_CONF_FILE" ]; then
  echo "Missing mysql custom confd file $NSSK_DB_CUSTOM_CONF_FILE"
  exit 1
fi

# database_setup
DB_SETUP_SCRIPT_DIR="$PROJECT_ROOT/database_setup"
if [ ! -d "$DB_SETUP_SCRIPT_DIR" ]; then
  echo "Missing database setup scripts directory $DB_SETUP_SCRIPT_DIR"
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

########################
# read parameters

CONTAINER_NAME="$(jq -r '.container_name' < "$CONFIG_FILE")"
if [ "$CONTAINER_NAME" == "null" ] || [ -z "$CONTAINER_NAME" ]; then
  echo "container_name not readable from config"
  exit 1
fi

IMAGE_NAME="$(jq -r '.image_name' < "$CONFIG_FILE")"
if [ "$IMAGE_NAME" == "null" ] || [ -z "$IMAGE_NAME" ]; then
  echo "image_name not readable from config"
  exit 1
fi

DB_LISTEN_IP="$(jq -r '.network.listen_ip' < "$CONFIG_FILE")"
if [ "$DB_LISTEN_IP" == "null" ] || [ -z "$DB_LISTEN_IP" ]; then
  echo "network.listen_ip not readable from config"
  exit 1
fi

DB_LISTEN_PORT="$(jq -r '.network.listen_port' < "$CONFIG_FILE")"
if [ "$DB_LISTEN_PORT" == "null" ] || [ -z "$DB_LISTEN_PORT" ]; then
  echo "network.listen_port not readable from config"
  exit 1
fi

NETWORK_NAME="$(jq -r '.network.name' < "$CONFIG_FILE")"
if [ "$NETWORK_NAME" == "null" ] || [ -z "$NETWORK_NAME" ]; then
  echo "network.name not readable from config"
  exit 1
fi

CONTAINER_SUBNET="$(jq -r '.network.container_subnet' < "$CONFIG_FILE")"
if [ "$CONTAINER_SUBNET" == "null" ] || [ -z "$CONTAINER_SUBNET" ]; then
  echo "network.container_subnet not readable from config"
  exit 1
fi

CONTAINER_GATEWAY="$(jq -r '.network.container_gateway' < "$CONFIG_FILE")"
if [ "$CONTAINER_GATEWAY" == "null" ] || [ -z "$CONTAINER_GATEWAY" ]; then
  echo "network.container_gateway not readable from config"
  exit 1
fi

SETUP_PASS="$(jq -r '.setup_pass' < "$CONFIG_FILE")"
if [ "$SETUP_PASS" == "null" ] || [ -z "$SETUP_PASS" ]; then
  echo "setup_pass not readable from config"
  exit 1
fi

CPU_COUNT="$(jq -r '.resources.cpu_count' < "$CONFIG_FILE")"
if [ "$CPU_COUNT" == "null" ] || [ -z "$CPU_COUNT" ]; then
  echo "resources.cpu_count not readable from config"
  exit 1
fi

MEMORY_AMT="$(jq -r '.resources.memory' < "$CONFIG_FILE")"
if [ "$MEMORY_AMT" == "null" ] || [ -z "$MEMORY_AMT" ]; then
  echo "resources.memory not readable from config"
  exit 1
fi

MEMORY_SWAP_AMT="$(jq -r '.resources.memory_swap' < "$CONFIG_FILE")"
if [ "$MEMORY_SWAP_AMT" == "null" ] || [ -z "$MEMORY_SWAP_AMT" ]; then
  echo "resources.memory_swap not readable from config"
  exit 1
fi

#########################
# database state

# native default port, container networking forwards a non-default port to this
MYSQL_PORT=3306

MYSQL_ROOT_PW_FILE="mysql.txt"

#DB_SETUP_SCRIPT="docker-entrypoint-initdb.d/0_nssk_setup.sql"

# data directory holding database fs state
DATA_DIR="$PROJECT_ROOT/mysql/data"
if [ ! -d "$DATA_DIR" ]; then
	mkdir -p "$DATA_DIR"
fi

# log directory
LOG_DIR="$PROJECT_ROOT/mysql/log"
if [ ! -d "$LOG_DIR" ]; then
	mkdir -p "$LOG_DIR"
fi

#########################
# network

# build network if it's not already built
echo "Building network"
if [[ -z $(docker network ls | grep "$NETWORK_NAME") ]]; then
	echo "Creating $NETWORK_NAME network"

	# TODO confirm success
	docker network create --driver=bridge --subnet="$CONTAINER_SUBNET" --gateway="$CONTAINER_GATEWAY" "$NETWORK_NAME"
else
	echo "Network $NETWORK_NAME exists. Skipping creation"
fi

# docker run will create the mounts if they don't already exist

# MySQL needs a decent amount of resources 2 cpu + 2.5g ram

# Always mount a volume for logs, even if logging is disabled.

# start container
echo "Starting container"
docker run\
 --name="$CONTAINER_NAME"\
 --network="$NETWORK_NAME"\
 -p "$DB_LISTEN_IP":"$DB_LISTEN_PORT":"$MYSQL_PORT"\
 --cpus="$CPU_COUNT"\
 --memory="$MEMORY_AMT"\
 --memory-swap="$MEMORY_SWAP_AMT"\
 -e MYSQL_ROOT_PASSWORD_FILE="/$MYSQL_ROOT_PW_FILE"\
 -v "$DATA_DIR":/var/lib/mysql\
 -v "$DB_CONFD_DIR":/etc/mysql/conf.d\
 -v "$LOG_DIR":/var/log/mysql\
 -d\
 "$IMAGE_NAME"

# TODO: may not always have logging enabled. add a switch for this or detect it from files in 'nssk-data/mysql'
# require logging enabled?

# wait on container healthcheck - can take a few minutes to start up
MAX_CHECKS=10
CHECK_COUNT=0

CONTAINER_HEALTHY=0
# Wait until the container becomes healthy or reach the maximum number of checks
until [ "$CHECK_COUNT" -ge "$MAX_CHECKS" ]; do
    # Retrieve the container's health status
    HEALTH_STATUS=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER_NAME")

    # Check if the container is healthy
    if [ "$HEALTH_STATUS" == "healthy" ]; then
        echo "Container $CONTAINER_NAME is healthy!"
        CONTAINER_HEALTHY=1
        break
    elif [ "$HEALTH_STATUS" == "starting" ]; then
        echo "Container $CONTAINER_NAME is still starting..."
    else
        echo "Container $CONTAINER_NAME is not healthy. Status: $HEALTH_STATUS"
        break
    fi

    # Increment the check count
    ((CHECK_COUNT++))

    # Wait for 10 seconds before checking again
    sleep 10
done

if [ $CONTAINER_HEALTHY == 1 ]; then
  echo "Container $CONTAINER_NAME reporting healthy. Continuing..."
else
  echo "Container $CONTAINER_NAME not reporting healthy. Exiting."
  exit 1
fi

# start fail2ban in container. requires mysql logging being enabled, and logs to be in place so wait for the database to fully start up.
# should be viable once the container is started and reporting healthy
# TODO selective startup of fail2ban based on whether or not we're starting mysql with logging
echo "Starting fail2ban" &&
docker exec -it "$CONTAINER_NAME" /etc/init.d/fail2ban start &&
sleep 10 &&
docker exec -it "$CONTAINER_NAME" /etc/init.d/fail2ban status &&
docker exec -it "$CONTAINER_NAME" /usr/bin/fail2ban-client status &&
echo "Removing setup script from container filesystem" &&
docker exec -it "$CONTAINER_NAME" rm -v /docker-entrypoint-initdb.d/1_create_users.sql &&

# the container needs this file on startup or restart
echo "Setting owner and permissions on cred file" &&
docker exec -it "$CONTAINER_NAME" chown root:root "$MYSQL_ROOT_PW_FILE" &&
docker exec -it "$CONTAINER_NAME" chmod 600 "$MYSQL_ROOT_PW_FILE"

# Confirm that 1_create_users.sql was deleted from /docker-entrypoint-initdb.d/
if docker exec -it "$CONTAINER_NAME" sh -c "test -f /docker-entrypoint-initdb.d/1_create_users.sql"; then
  echo "WARNING: Failed to delete /docker-entrypoint-initdb.d/1_create_users.sql from container filesystem."
else
  echo "Successfully deleted user setup script from container filesystem"
fi

# Confirm that mysql.txt was deleted from /
#if docker exec -it "$CONTAINER_NAME" sh -c "test -f /$MYSQL_ROOT_PW_FILE"; then
#  echo "WARNING: Failed to delete $MYSQL_ROOT_PW_FILE from container filesystem."
#else
#  echo "Successfully deleted cred file from container filesystem"
#fi

echo "Container startup completed. Move the config file and setup script to a secure location."
