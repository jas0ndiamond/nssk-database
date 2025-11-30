# NSSK Database

Stand up a containerized database to house NSSK data imported from its various sources.

---

### Setup
1. Ensure python3 is installed and available on the PATH
2. Run the environment setup script `./setup-env.sh`
3. Create database config file from the template in `nssk-database/setup/conf/db-setup.json.template`
4. Create fail2ban config files (`fail2ban.conf`, `jail.local`) and copy to `nssk-database/fail2ban`
5. Create a custom mysql config file `nssk-ext.cnf` from the template in `nssk-database/mysql/conf.d/nssk-ext.cnf.template`
6. Install `jq`: `sudo apt-get install jq`
7. Install and start docker.

---

### Start/Deploy container

Deploy the database using the provided shell script. Builds the image and runs the container.

`./deploy.sh /path/to/config.json`

Deploy a fresh instance of the database using the provided shell script. Stops a running database and purges existing state. Builds the image and runs the container.

`./redeploy.sh /path/to/config.json`

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

### Notes
* The MySQL database port is set up to be forwarded from 22306 by default.
* If the database is web-facing, configure router port-forwarding if necessary.
* If a container is stopped with `docker stop nssk-database`, it should be started with `docker start nssk-database`. 

---

### Backup and Restore
* [Backup and Restore](backup/README.md)
