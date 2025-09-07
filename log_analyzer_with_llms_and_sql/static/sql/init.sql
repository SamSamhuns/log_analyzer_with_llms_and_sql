-- database and table names are acquired from env variables
CREATE DATABASE IF NOT EXISTS `default`;
USE `default`;

-- create general file id table for all supported file types
CREATE TABLE IF NOT EXISTS `general_fid` (
    file_md5 VARCHAR(32) NOT NULL,
    inserted_date DATE NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    size FLOAT NOT NULL,

    PRIMARY KEY (file_md5)
);

-- create log file id table
CREATE TABLE IF NOT EXISTS `log_fid` (
    log_fid VARCHAR(32) NOT NULL,
    file_md5 VARCHAR(32) NOT NULL,
    inserted_date DATE NOT NULL,
    logfile_type VARCHAR(255) NOT NULL,
    size FLOAT NOT NULL,

    PRIMARY KEY (file_md5)
);

-- create anomaly detection log table
CREATE TABLE IF NOT EXISTS `anomaly_detection_log` (
    ID INT NOT NULL AUTO_INCREMENT,

    log_fid VARCHAR(32) NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    inference_time FLOAT NOT NULL,
    prediction INT NOT NULL,

    PRIMARY KEY (ID)
);


-- create rta worker switch log table
CREATE TABLE IF NOT EXISTS `rta_worker_switch_log` (
    ID INT NOT NULL AUTO_INCREMENT,

    log_fid VARCHAR(32) NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    goal_type VARCHAR(32) NOT NULL,
    rta_status INT NOT NULL,

    PRIMARY KEY (ID)
);