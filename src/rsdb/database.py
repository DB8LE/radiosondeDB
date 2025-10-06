import datetime
import logging
from typing import Any, Dict, List, Optional, Literal

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
CREATE TABLE IF NOT EXISTS meta (
serial VARCHAR(16) NOT NULL PRIMARY KEY,
sonde_type VARCHAR(16) NOT NULL,
subtype VARCHAR(16),
frame_count INT UNSIGNED NOT NULL,
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
burst_lat DECIMAL(9, 6),
burst_lon DECIMAL(9, 6),
burst_alt INT,
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

def search_sondes(
    cursor: mariadb.Cursor,
    serial: Optional[str] = None,
    data_fields: Optional[List[str]] = None,
    types: Optional[List[Literal["humidity", "pressure", "XDATA"]]] = None,
    min_frame_count: Optional[int] = None,
    date_start: Optional[datetime.date] = None,
    date_end: Optional[datetime.date] = None
) -> List[str]:
    """
    Search for sondes in the meta table.

    Search parameters:
    - serial: (with optional wildcard at the end using *)
    - data_fields: data fields that have to be available in flight data
    - types: filter allowed sonde types
    - min_frame_count: minimum frame_count
    - start_date: filter first_rx_time from this to end_date
    - end_date: filter first_rx time from start_date to this

    Returns a list of serials matching the parameters
    """
    sql = "SELECT serial FROM meta WHERE 1=1"
    params: List[Any] = []
    
    # Serial filter
    if serial:
        if serial.endswith('*'):
            pattern = serial[:-1] + '%'
        else:
            pattern = serial
        sql += " AND serial LIKE ?"
        params.append(pattern)

    if data_fields:
        for data_field in data_fields:
            sql += f" AND has_{data_field.lower()} = 1"

    # Types filter
    if types:
        placeholders = ", ".join(["?"] * len(types))
        sql += f" AND sonde_type IN ({placeholders})"
        params.extend(types)
    
    # Frame count filter
    if min_frame_count:
        sql += " AND frame_count >= ?"
        params.append(min_frame_count)

    # Date filters
    if date_start:
        sql += " AND first_rx_time >= ?"
        params.append(date_start)
    if date_end:
        sql += " AND first_rx_time <= ?"
        params.append(date_end)

    # Run query
    cursor.execute(sql, params)
    results = cursor.fetchall()

    # Fix mariadb result
    results = [tup[0] for tup in results]
    
    return results

