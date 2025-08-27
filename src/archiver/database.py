import logging
from typing import Dict, Any

import mariadb

def add_to_meta(first_packet: Dict[str, Any], burst_packet: None | Dict[str, Any], last_packet: Dict[str, Any]):
    """Add a flight to the metadata table by its first packet, last packet and optionally burst packet"""

    logging.info(f"Adding sonde '{first_packet["callsign"]}' to meta table")
    
def add_to_tracking(packet: Dict[str, Any]):
    """Add a packet to the tracking table"""

    logging.debug(f"Adding packet from sonde '{packet["callsign"]}' to tracking table")

def wipe_flight(serial: str):
    """Wipe a sonde flight from the tracking table"""

    logging.info(f"Wiping flight tracking data for sonde '{serial}'")
