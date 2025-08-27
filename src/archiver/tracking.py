import src.rsdb as rsdb
from . import database

import logging
from datetime import datetime, timezone
from typing import Dict, Any

import mariadb

class SondeTracker():
    """Process payload summaries received by radiosonde_auto_rx for a specific sonde"""

    def __init__(self, sonde_serial: str, db_cursor: mariadb.Cursor, min_frames: int, rx_timeout_seconds: int):
        self.sonde_serial = sonde_serial
        self.cursor = db_cursor
        self.min_frames = min_frames
        self.rx_timeout = rx_timeout_seconds

        self.total_frames = 0
        self.latest_packet_time = datetime.now(timezone.utc)

        self.latest_packet: rsdb.Packet
        self.first_packet: rsdb.Packet
        self.burst_packet: None | rsdb.Packet = None

    def close(self):
        """Close tracker specific cursor and remove self from tracked list"""

        logging.debug(f"Closing tracker for sonde '{self.sonde_serial}'")
        self.cursor.close()
        tracked_sondes.pop(self.sonde_serial)

    def update_timeout(self):
        """Update timeout to terminate if necessary"""

        # Check if timeout has been reached
        last_packet_seconds = (datetime.now(timezone.utc) - self.latest_packet_time).total_seconds()
        if last_packet_seconds >= self.rx_timeout:
            logging.info(f"Sonde '{self.sonde_serial}' has reached the rx timeout")

            # If flight hasn't reached the minimum required amount of frames, discard the flight
            if self.total_frames < self.min_frames:
                logging.info(f"Sonde '{self.sonde_serial}' has not reached the minimum amount of frames, deleting data")
                database.wipe_flight(self.sonde_serial)
                self.close()
                return
            
            # Add to meta table
            database.add_to_meta(self.first_packet, self.burst_packet, self.latest_packet)

            self.close()

    def handle_packet(self, packet: rsdb.Packet):
        """Handle a packet received via UDP from AutoRX"""

        self.total_frames += 1
        self.latest_packet = packet

        # TODO: Calculate speed and heading

        database.add_to_tracking(packet)
        logging.debug(f"Handling packet: {packet}")

        # Update latest packet time for rx timeout
        self.latest_packet_time = datetime.now(timezone.utc)

tracked_sondes: Dict[str, SondeTracker] = {} # Dict to store currently tracked sondes by their serials with the corresponding handler

def process_packet(packet: rsdb.Packet, db_conn: mariadb.Connection, min_frames: int, rx_timeout_seconds: int):
    """Process packet from AutoRX by passing it to sonde specific handlers"""

    # Check if sonde is already being tracked
    sonde_serial = packet.serial
    if sonde_serial not in tracked_sondes: # If no, do checks and add to tracked list
        # Check if sonde is already in DB (reception picked back up after timeout)
        query = "SELECT EXISTS (SELECT 1 FROM tracking WHERE serial = '?') AS value_exists;"
        cursor = db_conn.cursor()
        cursor.execute(query, (sonde_serial,))

        if cursor.fetchone()[0] == 1:
            logging.debug(f"New sonde '{sonde_serial}' already exists in DB. Skipping") # Log as debug to not spam info level logs

        # Sonde is new
        logging.info(f"Got new sonde '{sonde_serial}'")
        
        # Create tracker
        tracker = SondeTracker(sonde_serial, cursor, min_frames, rx_timeout_seconds)
        tracker.first_packet = packet
        tracked_sondes[sonde_serial] = tracker

        logging.info(f"Added new sonde '{sonde_serial}' to tracker list. Tracked list is now: {list(tracked_sondes.keys())}")

    # Send packet to tracker
    tracked_sondes[sonde_serial].handle_packet(packet)

def update_timeouts():
    """Update all sonde trackers timeouts"""

    serials = list(tracked_sondes.keys()).copy()
    for serial in serials:
        tracked_sondes[serial].update_timeout()

def close_trackers():
    """Close all trackers"""

    logging.debug("Closing all trackers")
    serials = list(tracked_sondes.keys()).copy()
    for serial in serials:
        tracked_sondes[serial].close()
