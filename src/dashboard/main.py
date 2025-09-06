import src.rsdb as rsdb
from . import dashboard

def main():
    rsdb.logging.set_up_logging("rsdb-dashboard") # Set up logging
    
    config = rsdb.config.read_config() # Read config
    rsdb.logging.set_logging_config(config) # Set logging config

    # Connect to DB
    database = rsdb.database.connect(config)
    database.autocommit = False

    # Start dashboard
    dash = dashboard.Dashboard(config["dashboard"]["port"], database.cursor())
    dash.run()
    