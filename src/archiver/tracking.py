import src.rsdb as rsdb
from . import database

import logging, traceback
from datetime import datetime, timezone
from typing import Dict

import mariadb, geopy.distance

class SondeTracker():
    """Process payload summaries received by radiosonde_auto_rx for a specific sonde"""

    def __init__(self, sonde_serial: str, db_cursor: mariadb.Cursor, min_frames: int, rx_timeout_seconds: int, min_frame_spacing: int):
        self.sonde_serial = sonde_serial
        self.cursor = db_cursor
        self.min_frames = min_frames
        self.rx_timeout = rx_timeout_seconds
        self.min_frame_spacing = min_frame_spacing

        self.total_frames = 0

        self.latest_packet: rsdb.Packet
        self.first_packet: rsdb.Packet
        self.burst_packet: None | rsdb.Packet = None

    def close(self):
        """Close tracker specific cursor and remove self from tracked list"""

        logging.info(f"Closing tracker for sonde '{self.sonde_serial}'")
        self.cursor.close()
        tracked_sondes.pop(self.sonde_serial)

    def update_timeout(self):
        """Update timeout to terminate if necessary"""

        # Check if timeout has been reached
        assert self.latest_packet.datetime is not None # should never happen
        last_packet_seconds = (datetime.now(timezone.utc) - self.latest_packet.datetime).total_seconds()
        if last_packet_seconds >= self.rx_timeout:
            logging.info(f"Sonde '{self.sonde_serial}' has reached the rx timeout with {self.total_frames} frames")

            # If flight hasn't reached the minimum required amount of frames, discard the flight
            if self.total_frames < self.min_frames:
                logging.info(f"Sonde '{self.sonde_serial}' has not reached the minimum amount of frames, deleting data")
                database.wipe_flight(self.cursor, self.sonde_serial)
                self.close()
                return
            
            # Calculate missing speed values
            if self.total_frames > 1:
                database.calculate_speed_values(self.cursor, self.sonde_serial)

            # Get burst point
            self.burst_packet = database.find_burst_point(self.cursor, self.sonde_serial)

            # Add to meta table
            database.add_to_meta(self.cursor, self.first_packet, self.burst_packet, self.latest_packet, self.total_frames)

            self.close()

    def handle_packet(self, packet: rsdb.Packet):
        """Handle a packet received via UDP from AutoRX"""

        # Check if minimum time between packets has been reached, unless packet is first packet
        assert packet.datetime is not None # should never fail
        assert self.latest_packet.datetime is not None # should also never fail
        if packet != self.first_packet:
            last_packet_time_delta = (packet.datetime - self.latest_packet.datetime).total_seconds()
            if round(last_packet_time_delta, 1) < self.min_frame_spacing:
                return

        # Filter packets by velocity (>300m/s shouldn't be possible without a broken packet)
        if packet != self.first_packet:
            prev_position = (self.latest_packet.latitude, self.latest_packet.longitude)
            position = (packet.latitude, packet.longitude)
            distance = geopy.distance.geodesic(prev_position, position).meters
            velocity = distance / last_packet_time_delta # type: ignore
            if velocity > 300:
                logging.info(f"Discarded invalid packet from sonde '{self.sonde_serial}' (velocity {round(velocity, 1)} m/s)")
                return

        # Add to DB
        #logging.debug(f"Handling packet: {packet}") # TODO: remove this
        database.add_to_tracking(self.cursor, packet)

        # Increment frame counter and set latest packet
        self.total_frames += 1
        self.latest_packet = packet

tracked_sondes: Dict[str, SondeTracker] = {} # Dict to store currently tracked sondes by their serials with the corresponding handler

def process_packet(packet: rsdb.Packet, db_conn: mariadb.Connection, min_frames: int, rx_timeout_seconds: int, min_frame_spacing: int):
    """Process packet from AutoRX by passing it to sonde specific handlers"""

    # Set packet datetime using date from RTC and time from UDP packet
    packet.datetime = datetime.now(timezone.utc)
    
    # Remove type prefix from serial (to match sondehub's serial format)
    if packet.serial[:3] == "DFM":
        packet.serial = packet.serial[4:]
    elif packet.serial[:4] == "IMET":
        packet.serial = packet.serial[5:]
    elif packet.serial[:3] == "M10":
        packet.serial = packet.serial[4:]
    elif packet.serial[:3] == "M20":
        packet.serial = packet.serial[4:]
    # TODO: are there more of these?

    # Remove suffix from main type
    if packet.type is not None: # theoretically shouldn't happen but who knows
        if packet.type[-4:] == "-SGP":
            packet.type = packet.type[:4]
        elif packet.type[-3:] == "-SG":
            packet.type = packet.type[:3]
        # TODO: are there more of these?

    # Check if sonde is already being tracked
    if packet.serial not in tracked_sondes: # If no, do checks and add to tracked list
        # Check if sonde is already in DB (reception picked back up after timeout)
        query = "SELECT EXISTS (SELECT 1 FROM tracking WHERE serial = ?) AS value_exists;"
        cursor = db_conn.cursor()
        cursor.execute(query, (packet.serial,))

        if cursor.fetchone()[0] == 1:
            logging.debug(f"New sonde '{packet.serial}' already exists in DB. Skipping") # Log as debug to not spam info level logs
            return

        # Sonde is new
        logging.info(f"Got new sonde '{packet.serial}'")
        
        # Create tracker
        tracker = SondeTracker(packet.serial, cursor, min_frames, rx_timeout_seconds, min_frame_spacing)
        tracker.first_packet = packet
        tracker.latest_packet = packet
        tracked_sondes[packet.serial] = tracker

        logging.info(f"Added new sonde '{packet.serial}' to tracker list. Tracked list is now: {list(tracked_sondes.keys())}")

    # Send packet to tracker
    try:
        tracked_sondes[packet.serial].handle_packet(packet)
    except Exception as e:
        logging.error(f"Encountered exception while processing packet in tracker for sonde '{packet.serial}': {e}\nClosing tracker and continuing.")
        logging.info(traceback.format_exc()) # Log as info to prevent having to reproduce with debug logging on
        try: # Try to close remaining parts of tracker in try except incase something is already closed
            tracked_sondes[packet.serial].close()
        except Exception:
            pass

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
