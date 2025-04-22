FROM mysql:8.0-debian

ENV TZ="America/Vancouver"

LABEL org.opencontainers.image.authors="jason.a.diamond@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update &&  \
    apt-get install --install-recommends -y apt-utils && \
    apt-get install --install-recommends -y logrotate fail2ban less procps tzdata rsyslog locales cron && \
    apt-get clean all && rm -rf /var/lib/apt/lists/*

# disable kernel logging within the container
RUN sed -i '/module(load="imklog")/s/^/#/' /etc/rsyslog.conf

# mysql cred file
ADD --chown=mysql:mysql ./database_setup/mysql.txt /
RUN chmod 600 /mysql.txt

# logrotate.d
ADD ./logrotate.d/mysqld-nssk /etc/logrotate.d/

# fail2ban config for mysql
ADD ./fail2ban/jail.local /etc/fail2ban/
ADD ./fail2ban/fail2ban.conf /etc/fail2ban/

# create log folder. mysql owns log directory.
RUN mkdir /var/log/mysql
RUN chown mysql:mysql /var/log/mysql

# database setup scripts
ADD --chown=mysql:mysql ./database_setup/0_create_dbs.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/1_create_users.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/2_create_nssk_cosmo_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/3_create_cnv_flowworks_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/4_create_dnv_flowworks_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/5_create_conductivity_rainfall_correlation_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/6_create_rainfall_event_data_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/7_create_waterrangers_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/8_create_cnv_hydrometric_tables.sql /docker-entrypoint-initdb.d

# mysql cnf files - both are required
# also add any other .cnf files
#root owns these resources and mysql user is allowed to read
ADD --chown=root:root ./mysql/conf.d/nssk.cnf /etc/mysql/conf.d/
ADD --chown=root:root ./mysql/conf.d/nssk-ext.cnf /etc/mysql/conf.d/
ADD --chown=root:root ./mysql/conf.d/*.cnf /etc/mysql/conf.d/
RUN chmod 644 /etc/mysql/conf.d/*.cnf

# won't work until mysql logs are created on fs
#RUN service fail2ban start

# seeing odd permissions by default. set explicitly
RUN chown mysql:mysql /run/mysqld
RUN chmod 750 /run/mysqld

# database port
EXPOSE 3306

# healthcheck - container typically takes a minute to fully startup
# TODO - proper implementation with mysqladmin_ping and auth
HEALTHCHECK --interval=60s --timeout=5s --retries=5 CMD timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' || exit 1
