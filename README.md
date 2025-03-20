# NSSK Database

Stand up a containerized database to house NSSK data imported from its various sources.

---

### Build Container

```
cd nssk-database
./build.sh /path/to/config.json
```

### Start Container

Create root pw file

Creates network 9.9.1.0



```
cd nssk-database
./start.sh /path/to/config.json
```

The MySQL database port set up to be forwarded by default.
If the database is web-facing, configure router port-forwarding if necessary.

---

### Purge

Purges database state and spins up a new, empty database.

```
cd nssk-database
./redeploy.sh /path/to/config.json
```

---

### Backups

* Create a backup
  * cronjob
* Restore from backup
  * With `nssk-admin` user
