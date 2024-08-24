-- database and table names are acquired from env variables
CREATE DATABASE IF NOT EXISTS `default`;
USE `default`;

-- create LOG table
CREATE TABLE IF NOT EXISTS log_anomaly (
    ID INT NOT NULL AUTO_INCREMENT,

    timestamp DATE NOT NULL,
    inf_time FLOAT NOT NULL,
    prediction INT NOT NULL,

    PRIMARY KEY (ID)
);