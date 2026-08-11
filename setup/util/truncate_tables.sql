-- these will need drop privilege
-- table/database list must match src/generate_db_setup.py's DATABASES and
-- per-dataset site lists - verified against a real restored backup 2026-08-11.

-- cnv rainfall
truncate table NSSK_CNV_FLOWWORKS.CNVRain;

-- dnv flowworks
truncate table NSSK_DNV_FLOWWORKS.DNV;

-- cosmo
truncate table NSSK_COSMO.HAST01;
truncate table NSSK_COSMO.HAST02;
truncate table NSSK_COSMO.HAST03;
truncate table NSSK_COSMO.MACK02;
truncate table NSSK_COSMO.MACK03;
truncate table NSSK_COSMO.MACK04;
truncate table NSSK_COSMO.MACK05;
truncate table NSSK_COSMO.MISS01;
truncate table NSSK_COSMO.MOSQ01;
truncate table NSSK_COSMO.MOSQ02;
truncate table NSSK_COSMO.MOSQ03;
truncate table NSSK_COSMO.MOSQ04;
truncate table NSSK_COSMO.MOSQ05;
truncate table NSSK_COSMO.MOSQ06;
truncate table NSSK_COSMO.MOSQ07;
truncate table NSSK_COSMO.WAGG01;
truncate table NSSK_COSMO.WAGG02;
truncate table NSSK_COSMO.WAGG03;

-- conductivity rainfall correlation
truncate table NSSK_CONDUCTIVITY_RAINFALL_CORRELATION.WAGG01;
truncate table NSSK_CONDUCTIVITY_RAINFALL_CORRELATION.WAGG02;
truncate table NSSK_CONDUCTIVITY_RAINFALL_CORRELATION.WAGG03;

-- rainfall event data
truncate table NSSK_RAINFALL_EVENT_DATA.RAINFALL_EVENTS;
truncate table NSSK_RAINFALL_EVENT_DATA.WAGG01;
truncate table NSSK_RAINFALL_EVENT_DATA.WAGG03;

-- waterrangers
truncate table NSSK_WATERRANGERS.WAG_E_01;
truncate table NSSK_WATERRANGERS.WAG_E_02;
truncate table NSSK_WATERRANGERS.WAG_E_03;
truncate table NSSK_WATERRANGERS.WAG_E_05;
truncate table NSSK_WATERRANGERS.WAG_E_06a;
truncate table NSSK_WATERRANGERS.WAG_E_06b;
truncate table NSSK_WATERRANGERS.WAG_E_07;
truncate table NSSK_WATERRANGERS.WAG_M_01;
truncate table NSSK_WATERRANGERS.WAG_M_02;
truncate table NSSK_WATERRANGERS.WAG_M_03;
truncate table NSSK_WATERRANGERS.MIS_M_01;
truncate table NSSK_WATERRANGERS.MIS_E_01;
truncate table NSSK_WATERRANGERS.MIS_W_01;
truncate table NSSK_WATERRANGERS.WAG_W_02a;
truncate table NSSK_WATERRANGERS.WAG_W_02b;
truncate table NSSK_WATERRANGERS.WAG_W_03;
truncate table NSSK_WATERRANGERS.MOS_M_01;

-- cnv hydrometric
truncate table NSSK_CNV_HYDROMETRIC.WaggCreek;

-- rainfall interval data
truncate table NSSK_RAINFALL_INTERVAL_DATA.WAGG01;
truncate table NSSK_RAINFALL_INTERVAL_DATA.WAGG03;
