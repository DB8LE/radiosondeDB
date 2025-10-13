import logging
import socket
import traceback

import src.rsdb as rsdb

from . import tracking


def main():
    rsdb.logging.set_up_logging("rsdb-archiver") # Set up logging
    
    config = rsdb.config.read_config() # Read config
    rsdb.logging.set_logging_config(config) # Set logging config

    # Check for high timeout and warn user
    rx_timeout = config["archiver"]["rx_timeout"]
    if rx_timeout > 3600: # 1 hour threshhold
        logging.warning("The configured receive timeout is quite high. This will lead to " \
                        "large gaps in your received data. If you are okay with this, you can safely ignore this warning")
    elif rx_timeout > 7200: # 2 hour threshhold
        logging.error("The configured receive timeout of 2 hours or more is too high. Lower it, or if you're " \
                      "really really sure about this, edit the code and remove this check.")
        exit(1)

    # Connect to DB
    database = rsdb.database.connect(config)

    # Set up main listener
    logging.info(f"Starting AutoRX UDP listener on {config['autorx']['host']}:{config['autorx']['port']}")
    udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_socket.settimeout(1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        pass

    # Start listening and enter main loop
    udp_socket.bind((config["autorx"]["host"], config["autorx"]["port"]))
    try:
        while True:
            try: # Got data, update sondes and timeouts
                data = udp_socket.recv(1024)
                
                packet = rsdb.Packet().from_json(data)
                if packet is not None: # If packet isn't payload summary, dont process
                    tracking.process_packet(packet, database, config["archiver"]["min_frames"], rx_timeout, config["archiver"]["min_seconds_per_frame"])
                
                tracking.update_timeouts()
            except socket.timeout: # No data from AutoRX, only update timeouts
                tracking.update_timeouts()

            database.commit()
    except KeyboardInterrupt:
        logging.info("Got keyboard interrupt, shutting down..")

        tracking.close_trackers()
        logging.debug("Closing database connection")
        database.close()
        logging.debug("Closing AutoRX UDP listener")
        udp_socket.close()

    except Exception as e:
        logging.error("Got exception while running archiver:")
        logging.error(e)
        logging.info(traceback.format_exc())

        tracking.close_trackers()
        database.close()
        udp_socket.close()

        exit(1)