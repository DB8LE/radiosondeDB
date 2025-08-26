import src.rsdb as rsdb

import logging

def main():
    rsdb.logging.set_up_logging(True, "rsdb_archiver")

    logging.info("Hello World!")