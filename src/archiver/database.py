import src.rsdb as rsdb

import logging
from typing import Dict, Any

import mariadb

def add_to_meta(cursor: mariadb.Cursor, first_packet: rsdb.Packet, burst_packet: None | rsdb.Packet, latest_packet: rsdb.Packet, frame_count: int, frame_spacing: int):
    """Add a flight to the metadata table by its first packet, last packet and optionally burst packet"""

    logging.info(f"Adding sonde '{first_packet.serial}' to meta table")

    # Check what "extras" the flight has
    has_humidity = latest_packet.humidity != None
    has_pressure = latest_packet.pressure != None
    has_battery = latest_packet.battery != None
    has_burst_timer = latest_packet.burst_timer != None
    has_xdata = latest_packet.xdata != None

    # Set burst packet data to none if no burst packet was provided
    if burst_packet == None:
        burst_time = None
        burst_lat = None
        burst_lon = None
        burst_alt = None
    else:
        burst_time = burst_packet.datetime
        burst_lat = burst_packet.latitude
        burst_lon = burst_packet.longitude
        burst_alt = burst_packet.altitude

    # Round frequency
    frequency = None if latest_packet.frequency is None else round(latest_packet.frequency, 2)

    # Insert into DB
    cursor.execute("INSERT INTO meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                   (first_packet.serial, latest_packet.type, latest_packet.subtype, frame_count, frame_spacing,
                    has_humidity, has_pressure, has_battery, has_burst_timer, has_xdata, frequency,
                    first_packet.datetime, first_packet.latitude, first_packet.longitude, first_packet.altitude,
                    latest_packet.datetime, latest_packet.latitude, latest_packet.longitude, latest_packet.altitude,
                    burst_time, burst_lat, burst_lon, burst_alt, latest_packet.rs41_mainboard, latest_packet.rs41_mainboard_fw,))
    
def add_to_tracking(cursor: mariadb.Cursor, packet: rsdb.Packet):
    """Add a packet to the tracking table"""

    logging.debug(f"Adding packet from sonde '{packet.serial}' to tracking table")
    cursor.execute("INSERT INTO tracking VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                   (packet.serial, packet.frame, packet.datetime, packet.latitude, packet.longitude, 
                    packet.altitude, packet.temperature, packet.humidity, packet.pressure, packet.speed, 
                    packet.battery, packet.burst_timer, packet.xdata,))

def wipe_flight(cursor: mariadb.Cursor, serial: str):
    """Wipe a sonde flight from the tracking table"""

    logging.info(f"Wiping flight tracking data for sonde '{serial}'")
    cursor.execute("DELETE FROM tracking WHERE serial = ?;", (serial,))
