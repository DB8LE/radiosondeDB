import src.rsdb as rsdb
from . import map


def main():
    rsdb.logging.set_up_logging("rsdb-map") # Set up logging
    
    config = rsdb.config.read_config() # Read config
    rsdb.logging.set_logging_config(config) # Set logging config

    # Connect to DB
    database = rsdb.database.connect(config)

    # Start map
    dash = map.Map("map", config["map"], config["maptiles"], database)
    dash.run()
    