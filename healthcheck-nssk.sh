#!/bin/bash

# Prefers an authenticated ping over TCP to 127.0.0.1 (proves the actual interface
# every real client uses is working - mysqladmin with no -h defaults to the Unix
# socket, which stays up even if the TCP listener is broken). Falls back to a plain
# TCP connect check if the healthcheck credentials file isn't present (e.g. this
# image run outside the documented compose flow, without the secret mounted), so a
# missing credentials file doesn't make an otherwise healthy server report
# unhealthy forever.

if [ -f /run/mysql-healthcheck.cnf ]; then
  exec mysqladmin --defaults-extra-file=/run/mysql-healthcheck.cnf -h 127.0.0.1 ping
else
  exec timeout 3 bash -c '</dev/tcp/127.0.0.1/3306'
fi
