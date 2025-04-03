# Backup and Restore

---
### Setup

Ensure the jq, gzip, and mysql-client are installed on your system, and `mysqldump`, `gzip`, and `jq` binaries are available on the PATH.
```
sudo apt-get install mysql-client jq gzip
-or-
sudo yum install mysql jq gzip
```

---
### Backup

Invoke the `./backup.sh` script to make a backup of the NSSK database instance.

```
./backup.sh /path/to/backup/dir /path/to/configs/config.json`
```

---
### Backup Management

Use the `trim_backups.sh` script to delete the oldest backups:

```
./trim_backups.sh /path/to/backup/dir
```

Typically run in a cronjob, after any backup operation completes.

---
### Restore

Use the `restore.sh` script to restore a backup to a fresh/empty NSSK database instance.

```
./restore.sh /path/to/configs/config.json /path/to/backup/backup_12345.sql
```
