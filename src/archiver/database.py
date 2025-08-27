import src.rsdb as rsdb

import logging
from typing import Dict, Any

import mariadb

def add_to_meta(first_packet: rsdb.Packet, burst_packet: None | rsdb.Packet, last_packet: rsdb.Packet):
    """Add a flight to the metadata table by its first packet, last packet and optionally burst packet"""

    logging.info(f"Adding sonde '{first_packet.serial}' to meta table")
    
def add_to_tracking(packet: rsdb.Packet):
    """Add a packet to the tracking table"""

    logging.debug(f"Adding packet from sonde '{packet.serial}' to tracking table")

def wipe_flight(serial: str):
    """Wipe a sonde flight from the tracking table"""

    logging.info(f"Wiping flight tracking data for sonde '{serial}'")
