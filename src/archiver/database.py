import logging
from typing import Dict

import geopy.distance
import mariadb

import src.rsdb as rsdb


def add_to_meta(cursor: mariadb.Cursor, first_packet: rsdb.Packet, burst_packet: None | rsdb.Packet, latest_packet: rsdb.Packet, frame_count: int):
    """Add a flight to the metadata table by its first packet, last packet and optionally burst packet"""

    logging.info(f"Adding sonde '{first_packet.serial}' to meta table")

    # Check what "extras" the flight has
    has_humidity = latest_packet.humidity is not None
    has_pressure = latest_packet.pressure is not None
    has_battery = latest_packet.battery is not None
    has_burst_timer = latest_packet.burst_timer is not None
    has_xdata = latest_packet.xdata is not None

    # Set burst packet data to none if no burst packet was provided
    if burst_packet is None:
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
    cursor.execute("INSERT INTO meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                   (first_packet.serial, latest_packet.type, latest_packet.subtype, frame_count,
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

def find_burst_point(cursor: mariadb.Cursor, serial: str) -> rsdb.Packet | None:
    """Find the burst point of a flight. Returns None if flight doesn't have a burst point"""

    has_burst_point = True

    # Get maximum altitude
    cursor.execute("SELECT frame, latitude, longitude, altitude, time " \
                   "FROM tracking WHERE serial = ? ORDER BY altitude DESC LIMIT 1;",
                    (serial,))
    data = cursor.fetchone()

    # Try to get next and previous frame to ensure it is actually a burst
    cursor.execute("SELECT altitude FROM tracking WHERE serial = ? AND frame < ? AND altitude < ? ORDER BY frame DESC LIMIT 1;", (serial, data[0], data[3],))
    previous = cursor.fetchone()
    cursor.execute("SELECT altitude FROM tracking WHERE serial = ? AND frame < ? AND altitude < ? ORDER BY frame ASC LIMIT 1;", (serial, data[0], data[3],))
    next = cursor.fetchone()

    if (previous is None) or (next is None):
        has_burst_point = False

    # Format packet
    if has_burst_point:
        packet = rsdb.Packet()
        packet.serial = serial
        packet.frame = data[0]
        packet.latitude = data[1]
        packet.longitude = data[2]
        packet.altitude = data[3]
        packet.datetime = data[4]
        logging.debug(f"Found burst packet for sonde flight '{serial}': {packet}")
    else:
        logging.debug(f"Sonde flight '{serial}' has no burst point")
        packet = None

    return packet

def calculate_speed_values(cursor: mariadb.Cursor, serial: str):
    """Calculate missing speed for packets where it's not present for specified flight"""

    logging.info(f"Calculating missing speed values for flight '{serial}'")

    # Get all fackets from flight
    cursor.execute("SELECT frame, speed, latitude, longitude, time " \
                   "FROM tracking WHERE serial = ? ORDER BY frame;",
                    (serial,))
    packets = cursor.fetchall()

    # Calculate new speed values
    updated_values: Dict[int, float] = {} # List with frame numbers and updated speed
    for i, packet in enumerate(packets):
        if packet[1] is not None: # Skip packets that already have a speed value
            continue

        if i == 0: # First packet
            next_packet = packets[i+1]

            lat1 = packet[2]
            lon1 = packet[3]
            lat2 = next_packet[2]
            lon2 = next_packet[3]

            time_diff = (next_packet[4] - packet[4]).total_seconds()
        elif i == (len(packets)-1): # Last packet
            prev_packet = packets[i-1]

            lat1 = packet[2]
            lon1 = packet[3]
            lat2 = prev_packet[2]
            lon2 = prev_packet[3]

            time_diff = (packet[4] - prev_packet[4]).total_seconds()
        else: # Other packets
            prev_packet = packets[i-1]
            next_packet = packets[i+1]

            lat1 = prev_packet[2]
            lon1 = prev_packet[3]
            lat2 = prev_packet[2]
            lon2 = prev_packet[3]

            time_diff = (next_packet[4] - prev_packet[4]).total_seconds()

        # Calculate speed
        distance = geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).meters
        speed = distance / time_diff

        # Add new speed to dict
        updated_values[packet[0]] = round(speed, 1)

    if updated_values == {}: # If theres nothing to be done, log and return
        logging.info(f"All speed values in flight '{serial}' are already present")
    else: # Theres packets that need to be fixed
        logging.info(f"Setting speed for {len(updated_values)} packets in flight '{serial}'")

    # Update values in DB
    for frame, new_speed in updated_values.items():
        cursor.execute("UPDATE tracking SET speed = ? WHERE serial = ? AND frame = ?", (new_speed, serial, frame,))
