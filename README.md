# NSSK Database

Stand up a containerized MySQL 8.0 database to house NSSK data imported from its various sources, orchestrated with Docker Compose.

---

### Prerequisites
* `python3`
* [`jq`](https://jqlang.org/): `sudo apt-get install jq`
* Docker Engine and Docker Compose v2 (the `docker compose` plugin, not the legacy standalone `docker-compose`) — required for the non-Swarm file-based secrets and `mem_limit`/`memswap_limit` settings this project's `docker-compose.yml` uses.

---

### Setup
1. Run the environment setup script: `./setup-env.sh`. This creates a local Python venv (`venv/`) used to run `src/generate_db_setup.py`; `requirements.txt` currently has no dependencies.
2. Create a database config file from one of the templates in `setup/conf/` (`db-setup-local-access.json.template` for localhost-only access, `db-setup-lan-access.json.template` to also allow LAN access), e.g. `cp setup/conf/db-setup-local-access.json.template setup/conf/config.json`, then edit it — see [Config file schema](#config-file-schema) below. This file contains plaintext credentials; it's gitignored (`setup/conf/*.json`) and should be kept out of version control and readable only by whoever administers the database.
3. Create a custom MySQL config file `mysql/conf.d/nssk-ext.cnf` from the template `mysql/conf.d/nssk-ext.cnf.template` (gitignored — add any deployment-specific `[mysqld]` settings here; `mysql/conf.d/nssk.cnf`, which is committed, already sets the server timezone, `UTF8MB4`, disables InnoDB NUMA interleaving, and routes MySQL's error/slow/general logs to `/var/log/mysql/*` — required for `logrotate.d/mysqld-nssk`, and bind-mounted to the host for any future host-level log-watching).

---

### Config file schema

| Key | Description |
|---|---|
| `setup_user` / `setup_pass` | Bootstrap MySQL root user/password. `setup_pass` becomes the container's root password (via a Docker Compose secret — see [SECURITY.md](SECURITY.md)). |
| `users.internal.{nssk,nssk_import,nssk_backup,nssk_admin}` | Passwords for the four internal service accounts `generate_db_setup.py` creates (see below for what each can do). |
| `users.external.<name>` | Optional externally-reachable users. Each has `password`, `databases` (a list of DB names or `"*"` for all), and `privileges` (subset of `SELECT`/`UPDATE`/`INSERT` — anything else is silently skipped). Names matching `dummy-*` are treated as placeholders and skipped entirely. |
| `network.listen_ip` / `network.listen_port` | Host IP/port `backup.sh`/`restore.sh` connect to. **Must be kept in sync by hand**: `listen_ip` with `DB_LISTEN_IP` in `.env`, `listen_port` with `docker-compose.yml`'s `DB_LISTEN_PORT` default (`23306`) — none of these are generated from one source. |
| `network.local_network` | CIDR/host pattern (MySQL-style, e.g. `192.168.%.%`) granted to `nssk`/`nssk_import`/`nssk_backup`/`nssk_admin`. |
| `network.container_network` | CIDR/host pattern for the Docker network the container runs on (e.g. `9.9.1.%`); also granted to the internal users above. **Must be kept in sync by hand** with `docker-compose.yml`'s `CONTAINER_SUBNET` default. |
| `network.wan_network` | Host pattern (MySQL-style) external users are created under. The templates default this to `'%'` (any host) — narrow this and firewall accordingly before granting any external user WAN access. |

Image/container name, Docker network name/subnet/gateway, listen port, and CPU/memory limits are **not** generated from this file. `docker-compose.yml` reads them as `${VAR:-default}` — each has a built-in default (shown in the file) and can be overridden by adding the matching variable to `.env`, but nothing beyond `DB_LISTEN_IP` needs to be set there for a normal deploy. Edit `docker-compose.yml`'s defaults, or add overrides to `.env`, to change them.

Internal user privileges (fixed by `src/generate_db_setup.py`, not configurable):
* **`nssk`** — `SELECT` only, on all NSSK databases. General read access.
* **`nssk_import`** — `SELECT` plus `CREATE, INSERT, UPDATE, DELETE, DROP` on all NSSK databases. DROP is granted intentionally so import jobs can recreate tables cleanly; scope this account's use accordingly.
* **`nssk_backup`** — `SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, EVENT, USAGE` on all NSSK databases plus global `PROCESS`, for `mysqldump`.
* **`nssk_admin`** — `ALL PRIVILEGES` on all NSSK databases.
* **`healthcheck`** — no privileges beyond `USAGE`, `@127.0.0.1` only. Not config-driven (no `config.json` entry, random password generated at build time) — exists solely so the container `HEALTHCHECK` can authenticate over real TCP to prove the actual client-facing interface works, without depending on `root` (which has no `127.0.0.1` grant at all) or a config-driven user (whose network scope isn't guaranteed to include loopback).

---

### Generate config and deploy

`generate-config.sh` reads your config JSON and, via `src/generate_db_setup.py`, writes:
* `database_setup/0_create_dbs.sql` and `database_setup/2_*.sql`–`9_*.sql` — schema for each dataset (built into the image; no secrets).
* `database_setup/1_create_users.sql` — `CREATE USER`/`GRANT` statements with plaintext passwords. Bind-mounted into the container at runtime (`/docker-entrypoint-initdb.d/1_create_users.sql`), **not** built into the image.
* `database_setup/mysql.txt` — the MySQL root password, used as a Docker Compose file-based secret.
* `database_setup/healthcheck.txt` — a random password for the dedicated `healthcheck` user (see above), also a Docker Compose file-based secret.

`.env` is **not** generated — it's a static, checked-in file at the project root. By convention it only sets `DB_LISTEN_IP` (defaults to loopback-only, `127.0.0.1`); edit it directly to expose the database beyond this host. Everything else `docker-compose.yml` reads (`IMAGE_NAME`, `CONTAINER_NAME`, `DB_LISTEN_PORT`, `CONTAINER_SUBNET`, `CONTAINER_GATEWAY`, `NETWORK_NAME`, `CPU_COUNT`, `MEMORY_AMT`, `MEMORY_SWAP_AMT`) has a built-in default in `docker-compose.yml` itself and only needs an `.env` entry if you actually want to override it.

`./generate-config.sh setup/conf/config.json` — validates prerequisites and generates the files above without building/starting anything.

`./deploy.sh setup/conf/config.json` — runs `generate-config.sh`, then `docker compose up -d --build`. Use this for a normal (non-destructive) deploy or to pick up config/schema changes.

`./redeploy.sh setup/conf/config.json` — `docker compose down`, purges `./mysql/data` and `./mysql/log` (destructive — wipes all database state), then runs `deploy.sh`. Use this for a fresh instance.

---

### Stop / start a running container

```
docker compose stop
docker compose start
```

(`docker compose down` also works to stop and remove the container; the named volumes under `./mysql/` persist either way since they're host bind mounts, not managed by compose.) Because the container's supporting services (rsyslog, cron) are started from `entrypoint-nssk.sh` on every container start rather than as one-off post-`docker run` steps, a plain stop/start also restarts them correctly.

---

### Connecting to the database

Every TCP connection must use TLS — no per-user exceptions (see [SECURITY.md](SECURITY.md)). What this means depends on how you're connecting:

**Shell (`mysql`, `mysqldump`, `mysqladmin`, etc.)** — nothing to change for normal use. These negotiate TLS automatically (`--ssl-mode=PREFERRED` is the client default), and every script in this repo (`backup.sh`, `restore.sh`, `entrypoint-nssk.sh`, `healthcheck-nssk.sh`) already relies on that default and was verified working under TLS enforcement. The one thing that will now fail outright is a connection that explicitly disables TLS (`--ssl=0`, `--ssl-mode=DISABLED`) — the server refuses it (`ERROR 3159 (HY000): Connections using insecure transport are prohibited...`).

**Code libraries** — behavior is not uniform, and needs checking per library/version, not assumed:
* Libraries that wrap the real MySQL/MariaDB client library (Python `mysqlclient`/`MySQLdb`, PHP `mysqli`/PDO with `mysqlnd`, Ruby `mysql2`, Perl `DBD::mysql`) generally inherit the same opportunistic-TLS-by-default behavior as the CLI tools, so they're likely unaffected — but "likely" isn't "verified," so test the actual client before relying on it.
* Pure-language reimplementations (Python `PyMySQL`, Node.js `mysql`/`mysql2`, Go `go-sql-driver/mysql`) frequently do **not** attempt TLS unless it's explicitly configured (an `ssl=`/`tls=` connection parameter). Without that, they won't gracefully fall back — the server will simply refuse the plaintext attempt. If anything in the broader pipeline uses one of these, check its connection config explicitly.
* `SQLAlchemy` (or any other engine-agnostic layer) inherits whatever the underlying driver does — same caveat, one level removed.
* All internal/external accounts use `caching_sha2_password` (this server's own default auth plugin, not a project-specific choice) — safe and conventional, but older client library versions have had incomplete support for it. Worth checking alongside TLS support if a client fails to connect, since the two issues can look similar from the outside.

---

### `setup/` directory

* `setup/conf/*.json.template` — config file templates (see [Config file schema](#config-file-schema)).
* `setup/sql/<dataset>/*.sql.template` — per-dataset table schema, with `$SITE`/`$MONITORING_LOCATION_ID` placeholders substituted per-site by `src/generate_db_setup.py` to produce the generated `database_setup/*.sql` files.
* `setup/util/checks.sql` — ad-hoc read-only data-quality queries (out-of-range values, date ranges).
* `setup/util/reset_db.sql` — manual cleanup script; run as root. Drops all 4 internal users and all 8 NSSK databases, `IF EXISTS` throughout so it's safe to rerun.
* `setup/util/truncate_tables.sql` — truncates all tables across all 8 NSSK databases without dropping them.

---

### Backup and Restore
* [Backup and Restore](backup/README.md)

### Security
* [Security model / known limitations](SECURITY.md)
