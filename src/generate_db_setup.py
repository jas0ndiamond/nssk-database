import json
import os
import re
import sys
from pathlib import Path
from string import Template

# set up the nssk mysql database
#
# generates sql statements to run locally as root
# adds databases
# adds users
# configures remote access

# config file params
DB_SETUP_USER_KEY = 'setup_user'
DB_SETUP_USER_PASS_KEY = 'setup_pass'

# TODO: add to config file? Maybe not- each has a set of tables with variable schemas
# TODO: maybe add to config class, and an internal config file. may want it not in the repo to limit attack surface
NSSK_COSMO_DB = "NSSK_COSMO"
NSSK_DNV_FLOWWORKS_DB = "NSSK_DNV_FLOWWORKS"
NSSK_CNV_FLOWWORKS_DB = "NSSK_CNV_FLOWWORKS"
NSSK_CONDUCTIVITY_RAINFALL_CORRELATION_DB = "NSSK_CONDUCTIVITY_RAINFALL_CORRELATION"
NSSK_RAINFALL_EVENT_DATA_DB = "NSSK_RAINFALL_EVENT_DATA"
NSSK_WATERRANGERS_DB = "NSSK_WATERRANGERS"
NSSK_CNV_HYDROMETRIC_DB = "NSSK_CNV_HYDROMETRIC"
NSSK_RAINFALL_INTERVAL_DATA_DB = "NSSK_RAINFALL_INTERVAL_DATA"

DATABASES = [
    NSSK_COSMO_DB,
    NSSK_DNV_FLOWWORKS_DB,
    NSSK_CNV_FLOWWORKS_DB,
    NSSK_CONDUCTIVITY_RAINFALL_CORRELATION_DB,
    NSSK_RAINFALL_EVENT_DATA_DB,
    NSSK_WATERRANGERS_DB,
    NSSK_CNV_HYDROMETRIC_DB,
    NSSK_RAINFALL_INTERVAL_DATA_DB
]

NETWORK_KEY = "network"
LOCAL_NETWORK = "local_network"
CONTAINER_NETWORK = "container_network"  # configured on container host
WAN_NETWORK = "wan_network"

NSSK_USERS_KEY = "users"
NSSK_USERS_KEY_INTERNAL = "internal"
NSSK_USERS_KEY_EXTERNAL = "external"
NSSK_USERS_PASSWORD_KEY = "password"
NSSK_USERS_DATABASES_KEY = "databases"
ALL_DATABASES_MATCH = "*"
DUMMY_USER_REGEX = r'^dummy-*'
NSSK_USERS_PRIVILEGES_KEY = "privileges"

NSSK_USER = "nssk"
NSSK_IMPORT_USER = "nssk_import"
NSSK_BACKUP_USER = "nssk_backup"
NSSK_ADMIN_USER = "nssk_admin"

ALLOWED_EXTERNAL_PRIVILEGES = [
    "SELECT",
    "UPDATE",
    "INSERT"
]

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
rainfall_event_sites = [
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

cnv_hydrometric_sites = [
    "WaggCreek"
]

rainfall_interval_data_sites = [
    "WAGG01",
    "WAGG03"
]

#####################
# define resource paths

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
scriptfile_target_dir = "%s/database_setup" % project_root

# Dockerfile and start.sh expect these files. do not make configurable
create_db_scriptfile = "%s/0_create_dbs.sql" % scriptfile_target_dir
create_users_scriptfile = "%s/1_create_users.sql" % scriptfile_target_dir
create_nssk_cosmo_tables_scriptfile = "%s/2_create_nssk_cosmo_tables.sql" % scriptfile_target_dir
create_cnv_flowworks_tables_scriptfile = "%s/3_create_cnv_flowworks_tables.sql" % scriptfile_target_dir
create_dnv_flowworks_tables_scriptfile = "%s/4_create_dnv_flowworks_tables.sql" % scriptfile_target_dir
create_conductivity_rainfall_correlation_tables_scriptfile = "%s/5_create_conductivity_rainfall_correlation_tables.sql" % scriptfile_target_dir
create_rainfall_event_data_tables_scriptfile = "%s/6_create_rainfall_event_data_tables.sql" % scriptfile_target_dir
create_waterrangers_tables_scriptfile = "%s/7_create_waterrangers_tables.sql" % scriptfile_target_dir
create_cnv_hydrometric_tables_scriptfile = "%s/8_create_cnv_hydrometric_tables.sql" % scriptfile_target_dir
create_rainfall_interval_data_tables_scriptfile = "%s/9_create_rainfall_interval_data_tables.sql" % scriptfile_target_dir

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
create_cnv_hydrometric_tables = []
create_rainfall_interval_data_tables = []

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

    print("\tWriting db setup script to %s" % create_db_scriptfile)
    with open(create_db_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in db_setup_statements)

    print("\tWriting user setup script to %s" % create_users_scriptfile)
    with open(create_users_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in user_setup_statements)

    print("\tWriting NSSK CoSMo table setup script to %s" % create_nssk_cosmo_tables_scriptfile)
    with open(create_nssk_cosmo_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_nssk_cosmo_tables)

    print("\tWriting CNV Flowworks table setup script to %s" % create_cnv_flowworks_tables_scriptfile)
    with open(create_cnv_flowworks_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_cnv_flowworks_tables)

    print("\tWriting DNV Flowworks table setup script to %s" % create_dnv_flowworks_tables_scriptfile)
    with open(create_dnv_flowworks_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_dnv_flowworks_tables)

    print("\tWriting Conductivity Rainfall Correlation table setup script to %s" %
          create_conductivity_rainfall_correlation_tables_scriptfile)
    with open(create_conductivity_rainfall_correlation_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_conductivity_rainfall_correlation_tables)

    print("\tWriting Rainfall Event Data table setup script to %s" %
          create_rainfall_event_data_tables_scriptfile)
    with open(create_rainfall_event_data_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_rainfall_event_data_tables)

    print("\tWriting Waterrangers table setup script to %s" %
          create_waterrangers_tables_scriptfile)
    with open(create_waterrangers_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_waterrangers_tables)

    print("\tWriting CNV Hydrometric table setup script to %s" %
          create_cnv_hydrometric_tables_scriptfile)
    with open(create_cnv_hydrometric_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_cnv_hydrometric_tables)

    print("\tWriting Rainfall Interval Data table setup script to %s" %
          create_rainfall_interval_data_tables_scriptfile)
    with open(create_rainfall_interval_data_tables_scriptfile, 'w') as handle:
        handle.writelines("%s\n" % line for line in create_rainfall_interval_data_tables)

def check_config():
    ######################
    # check that our required users are defined with passwords

    if NSSK_USER not in config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL]:
        raise "NSSK_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_USER] is None or config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_USER] == "":
        raise "NSSK_USER password not defined in user config"

    if NSSK_IMPORT_USER not in config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL]:
        raise "NSSK_IMPORT_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_IMPORT_USER] is None or config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_IMPORT_USER] == "":
        raise "NSSK_IMPORT_USER password not defined in user config"

    if NSSK_BACKUP_USER not in config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL]:
        raise "NSSK_BACKUP_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_BACKUP_USER] is None or config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_BACKUP_USER] == "":
        raise "NSSK_BACKUP_USER password not defined in user config"

    if NSSK_ADMIN_USER not in config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL]:
        raise "NSSK_ADMIN_USER not defined in user config"
    elif config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_ADMIN_USER] is None or config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_ADMIN_USER] == "":
        raise "NSSK_ADMIN_USER password not defined in user config"


def create_root_pw_file():
    print("\tWriting NSSK root password file to %s" % create_mysql_root_cred_file)
    with open(create_mysql_root_cred_file, 'w') as handle:
        handle.writelines("%s\n" % config[DB_SETUP_USER_PASS_KEY])

    # no longer need password in memory
    config[DB_SETUP_USER_PASS_KEY] = None


# Create the databases used by the project by running the "create_databases.sql" script.
# Requires a user that can create databases.
def create_databases():
    # create our databases
    for dbname in DATABASES:
        db_setup_statements.append("create database %s;" % dbname)

    # remove test database
    db_setup_statements.append("DROP DATABASE IF EXISTS test;")
    db_setup_statements.append("DELETE FROM mysql.db WHERE Db = 'test';")

    # remove help
    db_setup_statements.append("DROP TABLE mysql.help_topic, mysql.help_category, mysql.help_relation, mysql.help_keyword;")

def generate_user_create_statement(user, network, secret):
    #TODO use REQUIRE SSL when certs are configured

    # new hashing method
    return "CREATE USER '%s'@'%s' IDENTIFIED WITH caching_sha2_password BY '%s';" % (
        user, network, secret
    )

def configure_external_users():
    user_setup_statements.append("-- External User Creation +++++++++++++++++++++")

    for user in config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL]:
        if re.match(DUMMY_USER_REGEX, user):
            print("\tIgnoring dummy external user: '%s'" % user)
        else:
            print("\tCreating external user: '%s'" % user)
            # "jason": {
            #     "password": "asdgasdgasghasdgs",
            #     "privileges": ["SELECT"]
            # },

            # network always wan
            user_setup_statements.append(
                generate_user_create_statement(
                    user,
                    config[NETWORK_KEY][WAN_NETWORK],
                    config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user][NSSK_USERS_PASSWORD_KEY]
                )
            )

    print("Database external user creation completed")

    ######################
    # set user privileges

    print("Configuring external user privileges")

    user_setup_statements.append("-- External User Privileges +++++++++++++++++++++")

    # external users
    for user in config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL]:

        if re.match(DUMMY_USER_REGEX, user):
            print("\tIgnoring privilege configuration for external dummy user: '%s'" % user)
        else:
            print("\tConfiguring privileges for external user: '%s'" % user)

            if (config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user][NSSK_USERS_DATABASES_KEY] == ALL_DATABASES_MATCH or
                config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user][NSSK_USERS_DATABASES_KEY][0] == ALL_DATABASES_MATCH
            ):
                databases = DATABASES.copy()
            else:
                databases = config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user][NSSK_USERS_DATABASES_KEY]

            for database in databases:
                for privilege in config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user][NSSK_USERS_PRIVILEGES_KEY]:
                    if privilege in ALLOWED_EXTERNAL_PRIVILEGES:
                        user_setup_statements.append(
                            "GRANT %s ON %s.* TO '%s'@'%s';" % (privilege, database, user, config[NETWORK_KEY][WAN_NETWORK])
                        )
                    else:
                        print("Skipping disallowed privilege '%s' for external user '%s'" % (privilege, user))

            # no longer need user data in memory
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_EXTERNAL][user] = None

def configure_internal_users():
    # nssk - standard read-only user for working with data
    # nssk_import - user for importing data from various sources
    # nssk_admin - user/db management
    # nssk_backup - user for executing backups with mysqldump

    ######################
    # create users

    print("Creating database internal users")

    user_setup_statements.append("-- Internal User Creation +++++++++++++++++++++")

    # create nssk user
    # access from LAN, container networks
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_USER,
            config[NETWORK_KEY][CONTAINER_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_USER]
        )
    )

    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_USER,
            config[NETWORK_KEY][LOCAL_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_USER]
        )
    )

    # create nssk_import
    # access from LAN, container networks
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_IMPORT_USER,
            config[NETWORK_KEY][LOCAL_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_IMPORT_USER]
        )
    )
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_IMPORT_USER,
            config[NETWORK_KEY][CONTAINER_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_IMPORT_USER]
        )
    )

    # create nssk_backup
    # access from LAN, container networks
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_BACKUP_USER,
            config[NETWORK_KEY][LOCAL_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_BACKUP_USER]
        )
    )
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_BACKUP_USER,
            config[NETWORK_KEY][CONTAINER_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_BACKUP_USER]
        )
    )

    # create nssk_backup
    # access from LAN, container networks
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_ADMIN_USER,
            config[NETWORK_KEY][LOCAL_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_ADMIN_USER]
        )
    )
    user_setup_statements.append(
        generate_user_create_statement(
            NSSK_ADMIN_USER,
            config[NETWORK_KEY][CONTAINER_NETWORK],
            config[NSSK_USERS_KEY][NSSK_USERS_KEY_INTERNAL][NSSK_ADMIN_USER]
        )
    )

    # no longer need user data in memory
    config[NSSK_USERS_KEY][NSSK_USER] = None
    config[NSSK_USERS_KEY][NSSK_IMPORT_USER] = None
    config[NSSK_USERS_KEY][NSSK_BACKUP_USER] = None
    config[NSSK_USERS_KEY][NSSK_ADMIN_USER] = None

    print("Database internal user creation completed")

    ######################
    # set user privileges

    print("Configuring internal user privileges")

    user_setup_statements.append("-- Internal User Privileges +++++++++++++++++++++")

    # allow nssk user select access to databases
    for database in DATABASES:
        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # allow nssk-import user select access to databases in case inserts need to make decisions
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT SELECT ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][CONTAINER_NETWORK]))

    # add write access for nssk-import.
    # DROP for truncation since some datasets need to be re-made each time
    # local and container networks only
    for database in DATABASES:
        user_setup_statements.append("GRANT CREATE, INSERT, UPDATE, DELETE, DROP ON %s.* TO '%s'@'%s';" %
                                     (database, NSSK_IMPORT_USER, config[NETWORK_KEY][LOCAL_NETWORK]))

        user_setup_statements.append("GRANT CREATE, INSERT, UPDATE, DELETE, DROP ON %s.* TO '%s'@'%s';" %
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


def extended_user_setup():
    # if using a non-root user to set up database, limit that user to only logging in on that host
    if config[DB_SETUP_USER_KEY] != 'root':
        user_setup_statements.append("DELETE FROM mysql.user WHERE User='%s' AND Host NOT IN "
                                     "('localhost', '127.0.0.1', '%s');" % (
                                         config[DB_SETUP_USER_KEY],
                                         config[NETWORK_KEY][CONTAINER_NETWORK]))

    # specifically limit root
    user_setup_statements.append("DELETE FROM mysql.user WHERE User='root' AND Host NOT IN "
                                 "('localhost', '127.0.0.1', '%s');" % config[NETWORK_KEY][CONTAINER_NETWORK])

    # remove any anonymous users
    user_setup_statements.append("DROP USER IF EXISTS ''@'localhost';")
    user_setup_statements.append("DROP USER IF EXISTS ''@'%';")


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

    for monitoring_location_id in rainfall_event_sites:
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

def setup_cnv_hydrometric_tables():
    table_template = Template(open("%s/setup/sql/cnv-hydrometric/cnv-hydrometric.sql.template" % project_root).read())

    # set the database to create the tables in
    create_cnv_hydrometric_tables.append("use %s;" % NSSK_CNV_HYDROMETRIC_DB)

    for site in cnv_hydrometric_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_cnv_hydrometric_tables.append(create_table_sql)

def setup_rainfall_interval_data_tables():
    table_template = Template(open("%s/setup/sql/rainfall-interval-data/rainfall-interval-data.sql.template" % project_root).read())

    # set the database to create the tables in
    create_rainfall_interval_data_tables.append("use %s;" % NSSK_RAINFALL_INTERVAL_DATA_DB)

    for site in rainfall_interval_data_sites:
        create_table_sql = table_template.substitute(SITE=site)
        create_rainfall_interval_data_tables.append(create_table_sql)

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

    # create users and apply permissions for users
    print("Creating NSSK users")
    configure_internal_users()
    configure_external_users()
    extended_user_setup()
    print("NSSK users created")

    ###########
    # Core datasets

    print("Creating database tables")

    # create cosmo sensor tables
    print("\tCreating CoSMo tables")
    setup_cosmo_tables()
    print("\tCoSMo tables created")

    # create dnv flowworks tables
    print("\tCreating DNV Flowworks tables")
    setup_dnv_flowworks_tables()
    print("\tDNV Flowworks tables completed")

    # create cnv flowworks tables
    print("\tCreating CNV Flowworks tables")
    setup_cnv_flowworks_tables()
    print("\tCNV Rainfall tables completed")

    # create waterrangers tables
    print("\tCreating Waterrangers tables")
    setup_waterrangers_tables()
    print("\tWaterrangers tables completed")

    # create cnv hydrometric tables
    print("\tCreating CNV Hydrometric tables")
    setup_cnv_hydrometric_tables()
    print("\tCNV Hydrometric tables completed")

    ###########
    # Generative and computed datasets

    # create generative data tables
    print("\tCreating Conductivity-Rainfall Correlation tables")
    setup_conductivity_rainfall_correlation_tables()
    print("\tConductivity-Rainfall Correlation tables completed")

    print("\tCreating Rainfall Event Data tables")
    setup_rainfall_event_data_tables()
    print("\tRainfall Event Data tables completed")

    print("\tCreating Rainfall Interval Data tables")
    setup_rainfall_interval_data_tables()
    print("\tRainfall Interval Data tables completed")

    print("Database table creation completed")

    ###########
    # write our setup script files
    print("Writing database scripts to script files")
    write_setup_scripts()
    print("Database script writes completed")

    # write the password file
    print("Creating NSSK root password file")
    create_root_pw_file()
    print("NSSK root password file created")

    print("Setup completed. Move your credentials file to a secure location.")


##############################
if __name__ == "__main__":
    main(sys.argv)
