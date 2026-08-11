#!/bin/bash

# Container entrypoint. Runs on every container start (not just first `docker run`),
# unlike the old start.sh, which ran these as one-off `docker exec` calls after the
# initial run and was silently skipped by a plain `docker start`/compose restart.
#
# Starts the supporting services (rsyslog, cron) that used to be started post-hoc
# from the host, tightens a couple of runtime permissions, then hands off to the
# official MySQL entrypoint so mysqld remains the container's foreground process.
#
# fail2ban was deliberately removed from this container (see README's Security
# model section) - it ran at the wrong network layer to be effective here. Proper
# integration belongs at the host level, watching the bind-mounted
# ./mysql/log/mysql-error.log and banning via the host's DOCKER-USER iptables
# chain; that's planned as future work, not part of this container.

echo "[entrypoint-nssk] starting rsyslogd"
rsyslogd || echo "[entrypoint-nssk] WARNING: rsyslogd failed to start"

echo "[entrypoint-nssk] starting cron"
service cron start || echo "[entrypoint-nssk] WARNING: cron failed to start"

# mysqld's socket doesn't exist yet at this point (mysqld hasn't started). Poll for
# it in the background so this script can hand off to mysqld immediately instead
# of blocking startup.
(
  echo "[entrypoint-nssk] waiting for mysqld socket to tighten its permissions"
  for _ in $(seq 1 120); do
    sock="$(find /run/mysqld -maxdepth 1 -name '*.sock' 2>/dev/null | head -n1)"
    if [ -n "$sock" ]; then
      chmod 660 "$sock"
      echo "[entrypoint-nssk] tightened permissions on $sock"
      break
    fi
    sleep 1
  done
) &

# Write a short-lived, root-only defaults file so HEALTHCHECK can run an authenticated
# `mysqladmin ping` without a password ever appearing in a process listing. Uses the
# dedicated no-privilege healthcheck user, not root: root has no 127.0.0.1 grant at
# all (verified - it's deliberately localhost-socket-only), and a config-driven user
# would depend on the deployer's local_network happening to be 127.0.0.1, which isn't
# guaranteed. If this secret isn't mounted (e.g. a bare `docker run` outside compose),
# healthcheck-nssk.sh falls back to a plain TCP connect check instead of hard-failing.
if [ -f /run/secrets/healthcheck_password ]; then
  echo "[entrypoint-nssk] writing healthcheck credentials file"
  {
    echo "[client]"
    echo "user=healthcheck"
    printf 'password=%s\n' "$(cat /run/secrets/healthcheck_password)"
  } > /run/mysql-healthcheck.cnf
  chown root:root /run/mysql-healthcheck.cnf
  chmod 600 /run/mysql-healthcheck.cnf
else
  echo "[entrypoint-nssk] WARNING: /run/secrets/healthcheck_password not mounted, healthcheck will fall back to an unauthenticated TCP check"
fi

exec docker-entrypoint.sh "$@"
