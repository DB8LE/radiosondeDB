import logging
from typing import Dict, Any

import mariadb

CREATE_TRACKING_SQL = """
CREATE TABLE IF NOT EXISTS tracking (
serial VARCHAR(16) NOT NULL,
frame INT UNSIGNED NOT NULL,
time DATETIME NOT NULL,
latitude DECIMAL(9, 6) NOT NULL,
longitude DECIMAL(9, 6) NOT NULL,
altitude INT NOT NULL,
temperature DECIMAL(4, 1),
humidity DECIMAL(4, 1),
pressure DECIMAL(6, 2),
speed DECIMAL(4, 1),
battery DECIMAL(3, 1),
burst_timer MEDIUMINT,
xdata VARBINARY(256),
PRIMARY KEY(serial, time)
);
"""

CREATE_META_SQL = """
CREATE OR REPLACE TABLE meta (
serial VARCHAR(16) NOT NULL PRIMARY KEY,
sonde_type VARCHAR(16) NOT NULL,
subtype VARCHAR(16),
frame_count INT UNSIGNED NOT NULL,
frame_spacing TINYINT UNSIGNED NOT NULL,
has_humidity BOOLEAN NOT NULL,
has_pressure BOOLEAN NOT NULL,
has_battery BOOLEAN NOT NULL,
has_burst_timer BOOLEAN NOT NULL,
has_xdata BOOLEAN NOT NULL,
frequency DECIMAL(5, 2) UNSIGNED NOT NULL,
first_rx_time DATETIME NOT NULL,
first_rx_lat DECIMAL(9, 6) NOT NULL,
first_rx_lon DECIMAL(9, 6) NOT NULL,
first_rx_alt INT NOT NULL,
last_rx_time DATETIME NOT NULL,
last_rx_lat DECIMAL(9, 6) NOT NULL,
last_rx_lon DECIMAL(9, 6) NOT NULL,
last_rx_alt INT NOT NULL,
burst_time DATETIME,
burst_alt INT,
burst_lat DECIMAL(9, 6),
burst_lon DECIMAL(9, 6),
rs41_mainboard TEXT,
rs41_firmware TEXT
);
"""

def connect(config: Dict[str, Dict[str, Any]]) -> mariadb.Connection:
    """Get a connection to the database with the output of config.read_config() as the input while ensuring the needed tables exist."""

    # Get connection
    logging.info("Connecting to MariaDB")
    conn = mariadb.connect(**config["mariadb"])
    cursor = conn.cursor()

    # Ensure tables exist
    logging.debug("Ensuring MariaDB tables exist")
    cursor.execute(CREATE_TRACKING_SQL)
    cursor.execute(CREATE_META_SQL)
    cursor.close()

    return conn