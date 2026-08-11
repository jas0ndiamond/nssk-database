-- resets database state for testing setup
-- run as root
--
-- Host patterns (192.168.%.%, 9.9.1.%) match this environment's local_network/
-- container_network - update them if your config.json uses different values.
-- Database list must match src/generate_db_setup.py's DATABASES - verified
-- against a real restored backup 2026-08-11. IF EXISTS makes this safe to rerun;
-- no need for -f to skip expected failures.

drop user if exists nssk@'192.168.%.%';
drop user if exists nssk@'9.9.1.%';

drop user if exists nssk_admin@'192.168.%.%';
drop user if exists nssk_admin@'9.9.1.%';

drop user if exists nssk_backup@'192.168.%.%';
drop user if exists nssk_backup@'9.9.1.%';

drop user if exists nssk_import@'192.168.%.%';
drop user if exists nssk_import@'9.9.1.%';

drop database if exists NSSK_COSMO;
drop database if exists NSSK_DNV_FLOWWORKS;
drop database if exists NSSK_CNV_FLOWWORKS;
drop database if exists NSSK_CONDUCTIVITY_RAINFALL_CORRELATION;
drop database if exists NSSK_RAINFALL_EVENT_DATA;
drop database if exists NSSK_WATERRANGERS;
drop database if exists NSSK_CNV_HYDROMETRIC;
drop database if exists NSSK_RAINFALL_INTERVAL_DATA;
