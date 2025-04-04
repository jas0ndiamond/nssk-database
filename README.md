# NSSK Database

Stand up a containerized database to house NSSK data imported from its various sources.

---

### Setup

* Create database config file from the template in `nssk-database/setup/conf/db-setup.json.template`
* Create fail2ban config files (`fail2ban.conf`, `jail.local`) and copy to `nssk-database/fail2ban`
* Create a custom mysql config file `nssk.cnf` from the template in `nssk-database/mysql/conf.d/nssk.cnf.template`

---

### Stop a running container

```
docker stop nssk-database
```

---

### Start an already-built container

```
docker start nssk-database
```

---

### Scripts

Deploy the database. Builds the image and runs the container.

`./deploy.sh /path/to/config.json`

Deploy a fresh instance of the database. Stops a running database and purges existing state. Builds the image and runs the container.

`./redeploy.sh /path/to/config.json`

---

### Notes
* The MySQL database port set up to be forwarded from 22306 by default.
* If the database is web-facing, configure router port-forwarding if necessary.
* If a container is stopped with `docker stop nssk-database`, it should be started with `docker start nssk-database`. 

---

### Backup and Restore
* [Backup and Restore](backup/README.md)
