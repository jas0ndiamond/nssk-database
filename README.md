# NSSK Database

Stand up a containerized database to house NSSK data imported from its various sources.

---

### Setup

* Create db config file from the template in `nssk-database/setup/conf/db-setup.json.template`
* Create fail2ban config files (`fail2ban.conf`, `jail.local`) and copy to `nssk-database/fail2ban`

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

* The container creates network 9.9.1.0
* The MySQL database port set up to be forwarded from 22306 by default.
* If the database is web-facing, configure router port-forwarding if necessary.
* If a container is stopped with `docker stop nssk-database`, it should be started with `docker start nssk-database`. 

---

### Backups

* Create a backup
  * cronjob
* Restore from backup
  * With `nssk-admin` user
