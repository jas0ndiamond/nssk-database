import sys
import json
import os
from pathlib import Path
from string import Template

# set up the nssk mysql database
#
# generates sql statements to run locally as root
# adds databases
# adds users
# configures remote access

# config file params
DB_SETUP_USER = 'setup_user'
DB_SETUP_USER_PASS = 'setup_pass'

# TODO: add to config file? Maybe not- each has a set of tables with variable schemas
NSSK_COSMO_DB = "NSSK_COSMO"
NSSK_DNV_FLOWWORKS_DB = "NSSK_DNV_FLOWWORKS"
NSSK_CNV_FLOWWORKS_DB = "NSSK_CNV_FLOWWORKS"
NSSK_CONDUCTIVITY_RAINFALL_CORRELATION_DB = "NSSK_CONDUCTIVITY_RAINFALL_CORRELATION"
NSSK_RAINFALL_EVENT_DATA_DB = "NSSK_RAINFALL_EVENT_DATA"
NSSK_WATERRANGERS_DB = "NSSK_WATERRANGERS"
NSSK_CHLORIDE_ACUITY_DB = "NSSK_CHLORIDE_ACUITY"
NSSK_CNV_HYDROMETRIC_DB = "NSSK_CNV_HYDROMETRIC"

DATABASES = [
    NSSK_COSMO_DB,
    NSSK_DNV_FLOWWORKS_DB,
    NSSK_CNV_FLOWWORKS_DB,
    NSSK_CONDUCTIVITY_RAINFALL_CORRELATION_DB,
    NSSK_RAINFALL_EVENT_DATA_DB,
    NSSK_WATERRANGERS_DB,
    NSSK_CHLORIDE_ACUITY_DB,
    NSSK_CNV_HYDROMETRIC_DB
]

NETWORK_KEY = "network"
LOCAL_NETWORK = "local_network"
CONTAINER_NETWORK = "container_network"  # configured on container host
WAN_NETWORK = "wan_network"

NSSK_USERS_KEY = "users"
NSSK_USER = "nssk"
NSSK_IMPORT_USER = "nssk_import"
NSSK_BACKUP_USER = "nssk_backup"
NSSK_ADMIN_USER = "nssk_admin"

#####################

cosmo_monitoring_location_ids = [
    "WAGG01",
    "WAGG02",
    "WAGG03",
    "MOSQ01",
    "MOSQ02",
    "MOSQ03",
    "MOSQ04",
    "MOSQ05",
    "MOSQ06",
    "MOSQ07",
    "MISS01",
    "MACK02",
    "MACK03",
    "MACK04",
    "MACK05",
    "HAST01",
    "HAST02",
    "HAST03"
]

# rainfall sites. uses conductivity readings from these cosmo sites,
# along with rainfall data from CNV Flowworks CNVRain site
# TODO: map from cnv sites to cosmo sites
rainfall_sites = [
    "WAGG01",
    "WAGG03"
]

cnv_flowworks_sites = [
    "CNVRain"
]

dnv_flowworks_sites = [
    "DNV"
]

conductivity_rainfall_correlation_sites = [
    "WAGG01",
    "WAGG02",
    "WAGG03"
]

waterrangers_sites = [
    "WAG_E_01",
    "WAG_E_02",
    "WAG_E_03",
    "WAG_E_05",
    "WAG_E_06a",
    "WAG_E_06b",
    "WAG_E_07",
    "WAG_M_01",
    "WAG_M_02",
    "WAG_M_03",
    "MIS_M_01",
    "MIS_E_01",
    "MIS_W_01",
    "WAG_W_02a",
    "WAG_W_02b",
    "WAG_W_03",
    "MOS_M_01"
]

chloride_acuity_sites = [
    "WAGG01",
    "WAGG03"
]

cnv_hydrometric_sites = [
    "WaggCreek"
]

#####################

# Dockerfile and start.sh expect these files. do not make configurable
# TODO: check path exists
# TODO: switch to ../ from this file's location
# TODO: create project root from this file's location
project_root =".."
scriptfile_target_dir = "%s/database_setup" % project_root

create_db_scriptfile = "%s/0_create_dbs.sql" % scriptfile_target_dir
create_users_scriptfile = "%s/1_create_users.sql" % scriptfile_target_dir
create_nssk_cosmo_tables_scriptfile = "%s/2_create_nssk_cosmo_tables.sql" % scriptfile_target_dir
create_cnv_flowworks_tables_scriptfile = "%s/3_create_cnv_flowworks_tables.sql" % scriptfile_target_dir
create_dnv_flowworks_tables_scriptfile = "%s/4_create_dnv_flowworks_tables.sql" % scriptfile_target_dir
create_conductivity_rainfall_correlation_tables_scriptfile = "%s/5_create_conductivity_rainfall_correlation_tables.sql" % scriptfile_target_dir
create_rainfall_event_data_tables_scriptfile = "%s/6_create_rainfall_event_data_tables.sql" % scriptfile_target_dir
create_waterrangers_tables_scriptfile = "%s/7_create_waterrangers_tables.sql" % scriptfile_target_dir
create_chloride_acuity_tables_scriptfile = "%s/8_create_chloride_acuity_tables.sql" % scriptfile_target_dir
create_cnv_hydrometric_tables_scriptfile = "%s/9_create_cnv_hydrometric_tables.sql" % scriptfile_target_dir

create_mysql_root_cred_file = "%s/mysql.txt" % scriptfile_target_dir

#####################

config = {}
db_setup_statements = []
user_setup_statements = []
create_nssk_cosmo_tables = []
create_cnv_flowworks_tables = []
create_dnv_flowworks_tables = []
create_conductivity_rainfall_correlation_tables = []
create_rainfall_events_tables = []
create_rainfall_event_data_tables = []
create_waterrangers_tables = []
create_chloride_acuity_tables = []
create_cnv_hydrometric_tables = []

#############################

def write_setup_scripts():
    # check if the directory already exists
    if not os.path.exists(scriptfile_target_dir):
        # create the log dir if it doesn't exist
        Path(scriptfile_target_dir).mkdir(parents=True, exist_ok=True)

        # check that we succeeded
        if not os.path.exists(scriptfile_target_dir):
            e_msg = "Could not create database setup scripts directory '%s'." % scriptfile_target_dir
            print(e_msg)
            raise e_msg

    print("Writing db setup script to %s" % create_db_scriptfile)
    with open(create_db_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in db_setup_statements)

    print("Writing user setup script to %s" % create_users_scriptfile)
    with open(create_users_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in user_setup_statements)

    print("Writing NSSK CoSMo table setup script to %s" % create_nssk_cosmo_tables_scriptfile)
    with open(create_nssk_cosmo_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_nssk_cosmo_tables)

    print("Writing CNV Flowworks table setup script to %s" % create_cnv_flowworks_tables_scriptfile)
    with open(create_cnv_flowworks_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_cnv_flowworks_tables)

    print("Writing DNV Flowworks table setup script to %s" % create_dnv_flowworks_tables_scriptfile)
    with open(create_dnv_flowworks_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_dnv_flowworks_tables)

    print("Writing Conductivity Rainfall Correlation table setup script to %s" %
          create_conductivity_rainfall_correlation_tables_scriptfile)
    with open(create_conductivity_rainfall_correlation_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_conductivity_rainfall_correlation_tables)

    print("Writing Rainfall Event Data table setup script to %s" %
          create_rainfall_event_data_tables_scriptfile)
    with open(create_rainfall_event_data_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_rainfall_event_data_tables)

    print("Writing Waterrangers table setup script to %s" %
          create_waterrangers_tables_scriptfile)
    with open(create_waterrangers_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_waterrangers_tables)

    print("Writing Chloride Acuity table setup script to %s" %
          create_chloride_acuity_tables_scriptfile)
    with open(create_chloride_acuity_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_chloride_acuity_tables)

    print("Writing CNV Hydrometric table setup script to %s" %
          create_cnv_hydrometric_tables_scriptfile)
    with open(create_cnv_hydrometric_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_cnv_hydrometric_tables)

    print("Writing setup script completed")


def check_config():
    ######################
    # check that our required users are defined with passwords

    if NSSK_USER not in config[NSSK_USERS_KEY]:
        raise "NSSK_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_USER] is None or config[NSSK_USERS_KEY][NSSK_USER] == "":
        raise "NSSK_USER password not defined in user config"

    if NSSK_IMPORT_USER not in config[NSSK_USERS_KEY]:
        raise "NSSK_IMPORT_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_IMPORT_USER] is None or config[NSSK_USERS_KEY][NSSK_IMPORT_USER] == "":
        raise "NSSK_IMPORT_USER password not defined in user config"

    if NSSK_BACKUP_USER not in config[NSSK_USERS_KEY]:
        raise "NSSK_BACKUP_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_BACKUP_USER] is None or config[NSSK_USERS_KEY][NSSK_BACKUP_USER] == "":
        raise "NSSK_BACKUP_USER password not defined in user config"

    if NSSK_ADMIN_USER not in config[NSSK_USERS_KEY]:
        raise "NSSK_ADMIN_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_ADMIN_USER] is None or config[NSSK_USERS_KEY][NSSK_ADMIN_USER] == "":
        raise "NSSK_ADMIN_USER password not defined in user config"


def create_root_pw_file():
    print("Writing NSSK root password file to %s" % create_mysql_root_cred_file)
    with open(create_mysql_root_cred_file, 'w') as handle:
        handle.writelines("%s\n" % config[DB_SETUP_USER_PASS])

    # no longer need password in memory
    config[DB_SETUP_USER_PASS] = None


# Create the databases used by the project by running the "create_databases.sql" script.
# Requires a user that can create databases.
def create_databases():
    for dbname in DATABASES:
        db_setup_statements.append("create database %s;" % dbname)


def configure_users():
    # nssk - standard read-only user for working with data
    # nssk_import - user for importing data from various sources
    # nssk_admin - user/db management
    # nssk_backup - user for executing backups with mysqldump

    ######################
    # create users

    print("Creating database users")

    # create nssk user
    # access from WAN, LAN, container networks
    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_USER, config[NETWORK_KEY][WAN_NETWORK], config[NSSK_USERS_KEY][NSSK_USER]))

    # create nssk_import
    # access from LAN, container networks
    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_IMPORT_USER,
                                  config[NETWORK_KEY][LOCAL_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_IMPORT_USER])
                                 )

    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_IMPORT_USER,
                                  config[NETWORK_KEY][CONTAINER_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_IMPORT_USER])
                                 )

    # create nssk_backup
    # access from LAN, container networks
    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_BACKUP_USER,
                                  config[NETWORK_KEY][LOCAL_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_BACKUP_USER])
                                 )
    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_BACKUP_USER,
                                  config[NETWORK_KEY][CONTAINER_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_BACKUP_USER])
                                 )

    # create nssk_backup
    # access from LAN, container networks
    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_ADMIN_USER,
                                  config[NETWORK_KEY][LOCAL_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_ADMIN_USER]))

    user_setup_statements.append("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" %
                                 (NSSK_ADMIN_USER,
                                  config[NETWORK_KEY][CONTAINER_NETWORK],
                                  config[NSSK_USERS_KEY][NSSK_ADMIN_USER]))

    # no longer need passwords in memory
    config[NSSK_USERS_KEY][NSSK_USER] = None
    config[NSSK_USERS_KEY][NSSK_IMPORT_USER] = None
    config[NSSK_USERS_KEY][NSSK_BACKUP_USER] = None
    config[NSSK_USERS_KEY][NSSK_ADMIN_USER] = None

    print("Database user creation completed")

    ######################
    # set user privileges

    print("Configuring user privileges")

    # allow nssk user select access to databases
    for database in DATABASES:
        # WAN_NETWORK is a wildcard so should not need to add LOCAL_NETWORK and CONTAINER_NETWORK
        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" % (
            database,
            NSSK_USER,
            config[NETWORK_KEY][WAN_NETWORK])
                                     )

    # allow nssk-import user select access to databases in case inserts need to make decisions
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # add write access to cosmo_data for nssk-import
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append("GRANT CREATE, INSERT, UPDATE, DELETE ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT CREATE, INSERT, UPDATE, DELETE ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # allow nssk-admin write access
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_ADMIN_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_ADMIN_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # backup user permissions
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append(
            "GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, EVENT, USAGE ON %s.* TO '%s'@'%s';" %
            (database, NSSK_BACKUP_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append(
            "GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, EVENT, USAGE ON %s.* TO '%s'@'%s';" %
            (database, NSSK_BACKUP_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # backup needs global process privilege
    # local and container networks only
    user_setup_statements.append("GRANT PROCESS ON *.* TO '%s'@'%s';" %
                                 (NSSK_BACKUP_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

    user_setup_statements.append("GRANT PROCESS ON *.* TO '%s'@'%s';" %
                                 (NSSK_BACKUP_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    print("Configuration of user privileges complete")


def limit_remote_root_login():
    # if using a non-root user to set up database, limit that user to only logging in on that host
    if config[DB_SETUP_USER] != 'root':
        user_setup_statements.append("DELETE FROM mysql.user WHERE User='%s' AND Host NOT IN "
                                     "('localhost', '127.0.0.1', '%s');" % (
                                         config[DB_SETUP_USER],
                                         config[NETWORK_KEY][CONTAINER_NETWORK]))

    # specifically limit root
    user_setup_statements.append("DELETE FROM mysql.user WHERE User='root' AND Host NOT IN "
                                 "('localhost', '127.0.0.1', '%s');" % config[NETWORK_KEY][CONTAINER_NETWORK])


def setup_cosmo_tables():
    table_template = Template(open("%s/setup/sql/CoSMo/nssk-cosmo-sensor-table.sql.template" % project_root).read())

    # set the database to create the tables in
    create_nssk_cosmo_tables.append("use %s;" % NSSK_COSMO_DB)

    for monitoring_location_id in cosmo_monitoring_location_ids:
        create_table_sql = table_template.substitute(MONITORING_LOCATION_ID=monitoring_location_id)
        create_nssk_cosmo_tables.append(create_table_sql)


def setup_cnv_flowworks_tables():
    table_template = Template(open("%s/setup/sql/cnv-flowworks/nssk-cnv-flowworks.sql.template" % project_root).read())

    # set the database to create the tables in
    create_cnv_flowworks_tables.append("use %s;" % NSSK_CNV_FLOWWORKS_DB)

    for site in cnv_flowworks_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_cnv_flowworks_tables.append(create_table_sql)


def setup_dnv_flowworks_tables():
    table_template = Template(open("%s/setup/sql/dnv-flowworks/nssk-dnv-flowworks.sql.template" % project_root).read())

    # set the database to create the tables in
    create_dnv_flowworks_tables.append("use %s;" % NSSK_DNV_FLOWWORKS_DB)

    for site in dnv_flowworks_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_dnv_flowworks_tables.append(create_table_sql)


def setup_conductivity_rainfall_correlation_tables():
    # set the database to create the tables in
    create_conductivity_rainfall_correlation_tables.append("use %s;" % NSSK_CONDUCTIVITY_RAINFALL_CORRELATION_DB)

    table_template = Template(open(
        "%s/setup/sql/conductivity-rainfall-correlation/conductivity-rainfall-correlation.sql.template" % project_root).read())

    for monitoring_location_id in conductivity_rainfall_correlation_sites:
        create_table_sql = table_template.substitute(MONITORING_LOCATION_ID=monitoring_location_id)
        create_conductivity_rainfall_correlation_tables.append(create_table_sql)


def setup_rainfall_event_data_tables():
    # set the database to create the tables in
    create_rainfall_event_data_tables.append("use %s;" % NSSK_RAINFALL_EVENT_DATA_DB)

    # table for rainfall events. nothing to substitute
    with open("%s/setup/sql/rainfall-event-data/rainfall-events.sql.template" % project_root, 'r') as reader:
        create_rainfall_event_data_tables.append("".join(reader.readlines()))

    # event data tables for each site
    table_template = Template(open(
        "%s/setup/sql/rainfall-event-data/rainfall-event-data.sql.template" % project_root).read())

    for monitoring_location_id in rainfall_sites:
        create_table_sql = table_template.substitute(MONITORING_LOCATION_ID=monitoring_location_id)
        create_rainfall_event_data_tables.append(create_table_sql)


def setup_waterrangers_tables():
    # set the database to create the tables in
    create_waterrangers_tables.append("use %s;" % NSSK_WATERRANGERS_DB)

    # event data tables for each site
    table_template = Template(open(
        "%s/setup/sql/waterrangers/waterrangers-site.sql.template" % project_root).read())

    for site in waterrangers_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_waterrangers_tables.append(create_table_sql)

def setup_chloride_acuity_tables():
    table_template = Template(open("%s/setup/sql/chloride-acuity/chloride-acuity.sql.template" % project_root).read())

    # set the database to create the tables in
    create_chloride_acuity_tables.append("use %s;" % NSSK_CHLORIDE_ACUITY_DB)

    for site in chloride_acuity_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_chloride_acuity_tables.append(create_table_sql)

def setup_cnv_hydrometric_tables():
    table_template = Template(open("%s/setup/sql/cnv-hydrometric/cnv-hydrometric.sql.template" % project_root).read())

    # set the database to create the tables in
    create_cnv_hydrometric_tables.append("use %s;" % NSSK_CNV_HYDROMETRIC_DB)

    for site in cnv_hydrometric_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_cnv_hydrometric_tables.append(create_table_sql)

# this may not be necessary any more
# def setup_root_container_login():
#     # let root login from container network. meant to be temporary
#     # UPDATE mysql.user SET Host='9.9.1.%' WHERE Host='localhost' AND User='root';
#     # UPDATE mysql.db SET Host='9.9.1.%' WHERE Host='localhost' AND User='root';
#
#     if config[DB_SETUP_USER] != 'root':
#         setup_statements.append("UPDATE mysql.user SET Host='%s' WHERE Host='localhost' AND User='%s'" %
#                                 (config[DB_SETUP_USER], config[NETWORK_KEY][CONTAINER_NETWORK]))
#         setup_statements.append("UPDATE mysql.db SET Host='%s' WHERE Host='localhost' AND User='%s'" %
#                                 (config[DB_SETUP_USER], config[NETWORK_KEY][CONTAINER_NETWORK]))
#     # root specifically
#     setup_statements.append("UPDATE mysql.user SET Host='%s' WHERE Host='localhost' AND User='root'" %
#                             config[NETWORK_KEY][CONTAINER_NETWORK])
#     setup_statements.append("UPDATE mysql.db SET Host='%s' WHERE Host='localhost' AND User='root'" %
#                             config[NETWORK_KEY][CONTAINER_NETWORK])
#
#     pass


#####################################
def main(args):
    # find creds file from shell

    usage_msg = "Usage: python3 generate_db_setup.py db-setup.json\n"
    "\tdb-setup.json: file storing credentials for necessary users "
    "(nssk, nssk-import, nssk-admin, nssk-backup)"

    conf_file = None

    if len(args) == 2:
        if args[1] == "-h" or args[1] == "-help" or args[1] == "--help":
            print(usage_msg)
            exit(1)
        else:
            conf_file = args[1]
    else:
        print(usage_msg)
        exit(1)

    if conf_file is None:
        print("Failed to read conf_file\n%s" % usage_msg)

    ########
    # read config
    json_data = open(conf_file).read()

    global config
    config = json.loads(json_data)
    ########

    # check needed users are defined in conf file and have passwords

    print("Checking config...")
    check_config()
    print("Config check passed")

    # create databases

    print("Creating NSSK databases")
    create_databases()
    print("NSSK databases created")

    print("Creating NSSK root password file")
    create_root_pw_file()
    print("NSSK root password file created")

    # create users and apply permissions for users
    print("Creating NSSK users")
    configure_users()
    limit_remote_root_login()
    print("NSSK users created")

    ###########
    # Core datasets

    # create cosmo sensor tables
    print("Creating CoSMo tables")
    setup_cosmo_tables()
    print("CoSMo tables created")

    # create dnv flowworks tables
    print("Creating DNV Flowworks tables")
    setup_dnv_flowworks_tables()
    print("DNV Flowworks tables completed")

    # create cnv flowworks tables
    print("Creating CNV Flowworks tables")
    setup_cnv_flowworks_tables()
    print("CNV Rainfall tables completed")

    # create waterrangers tables
    print("Creating Waterrangers tables")
    setup_waterrangers_tables()
    print("Waterrangers tables completed")

    # create cnv hydrometric tables
    print("Creating CNV Hydrometric tables")
    setup_cnv_hydrometric_tables()
    print("CNV Hydrometric tables completed")

    ###########
    # Generative and computed datasets

    # create generative data tables
    print("Creating Conductivity-Rainfall Correlation tables")
    setup_conductivity_rainfall_correlation_tables()
    print("Conductivity-Rainfall Correlation tables completed")

    print("Creating Rainfall Event Data tables")
    setup_rainfall_event_data_tables()
    print("Rainfall Event Data tables completed")

    print("Creating Chloride Acuity tables")
    setup_chloride_acuity_tables()
    print("Chloride Acuity tables completed")

    ###########
    # write our setup script files
    write_setup_scripts()

    print("Setup completed. Move your credentials file to a secure location.")


##############################
if __name__ == "__main__":
    main(sys.argv)
