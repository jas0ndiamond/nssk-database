FROM mysql:8.0-debian

ENV TZ="America/Vancouver"

LABEL org.opencontainers.image.authors="jason.a.diamond@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update &&  \
    apt-get install --install-recommends -y apt-utils && \
    apt-get install --install-recommends -y logrotate less procps tzdata rsyslog locales cron && \
    apt-get clean all && rm -rf /var/lib/apt/lists/*

# disable kernel logging within the container
RUN sed -i '/module(load="imklog")/s/^/#/' /etc/rsyslog.conf

# logrotate.d
# ADD copies the build-context file's on-disk mode, which follows the deploying
# user's umask and can end up group/world-writable - logrotate refuses to process
# a config file it considers "world writable", so this has to be pinned explicitly.
ADD ./logrotate.d/mysqld-nssk /etc/logrotate.d/
RUN chmod 644 /etc/logrotate.d/mysqld-nssk

# create log folder. mysql owns log directory.
RUN mkdir /var/log/mysql
RUN chown mysql:mysql /var/log/mysql

# database setup scripts
# 1_create_users.sql is intentionally NOT added here - it contains plaintext user
# passwords and is bind-mounted into /docker-entrypoint-initdb.d at runtime by
# docker-compose.yml instead, so it never ends up in an image layer.
ADD --chown=mysql:mysql ./database_setup/0_create_dbs.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/2_create_nssk_cosmo_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/3_create_cnv_flowworks_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/4_create_dnv_flowworks_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/5_create_conductivity_rainfall_correlation_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/6_create_rainfall_event_data_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/7_create_waterrangers_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/8_create_cnv_hydrometric_tables.sql /docker-entrypoint-initdb.d
ADD --chown=mysql:mysql ./database_setup/9_create_rainfall_interval_data_tables.sql /docker-entrypoint-initdb.d

# mysql cnf files - both are required
# also add any other .cnf files
#root owns these resources and mysql user is allowed to read
ADD --chown=root:root ./mysql/conf.d/nssk.cnf /etc/mysql/conf.d/
ADD --chown=root:root ./mysql/conf.d/nssk-ext.cnf /etc/mysql/conf.d/
ADD --chown=root:root ./mysql/conf.d/*.cnf /etc/mysql/conf.d/
RUN chmod 644 /etc/mysql/conf.d/*.cnf

# seeing odd permissions by default. set explicitly
RUN chown mysql:mysql /run/mysqld
RUN chmod 750 /run/mysqld

# entrypoint - starts rsyslog/cron on every container start (not just the first
# `docker run`), then hands off to the official mysql entrypoint
ADD --chown=root:root ./entrypoint-nssk.sh /
RUN chmod 500 /entrypoint-nssk.sh
ENTRYPOINT ["/entrypoint-nssk.sh"]
# setting ENTRYPOINT above resets the base image's inherited CMD ["mysqld"] to
# empty - must be redeclared explicitly or docker-entrypoint.sh gets no arguments
CMD ["mysqld"]

ADD --chown=root:root ./healthcheck-nssk.sh /
RUN chmod 500 /healthcheck-nssk.sh

# database port
EXPOSE 3306

# healthcheck - probes TCP (the interface every real client uses), not the Unix
# socket (mysqladmin with no -h defaults to it, and it stays up even if the TCP
# listener is broken - verified). --start-period/--start-interval: measured a clean
# first-time init (8 databases + full schema) at ~55s, right at the edge of a plain
# 60s interval: probe every 5s for the first 2 minutes so a normal start reaches
# "healthy" quickly, without that grace period counting against --retries.
HEALTHCHECK --interval=60s --timeout=5s --retries=5 --start-period=120s --start-interval=5s \
  CMD /healthcheck-nssk.sh
