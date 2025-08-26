import logging, platform, sys

class CustomFormatter(logging.Formatter):
    """
    A custom logging formatter with the option to use ANSI escape codes for coloring the output.
    """

    def __init__(self, use_color=True):
        self.use_color = use_color

        # ANSI escape codes for coloring
        self.RESET  = "\x1b[0m"
        self.RED    = "\x1b[31m"
        self.YELLOW = "\x1b[33m"

        self.FORMAT = "[%(asctime)s] (%(levelchar)s) %(message)s"

        self.LEVEL_MAP = {
            logging.ERROR:   ("E", self.RED),
            logging.WARNING: ("W", self.YELLOW),
            logging.INFO:    ("I", ""),  # no color
            logging.DEBUG:   ("D", ""),  # no color
        }

    def format(self, record):
        levelno = record.levelno
        char, color = self.LEVEL_MAP.get(levelno, ("?", ""))

        # Inject new attributes into the record
        record.levelchar = char
        fmt = self.FORMAT
        if self.use_color:
            fmt = color + self.FORMAT + self.RESET
        formatter = logging.Formatter(fmt, "%H:%M:%S")

        return formatter.format(record)

def handle_uncaught(exc_type, exc_value, exc_tb):
    """A function to show uncaught exceptions by sending them to logging"""

    logging.log(logging.ERROR, "Unhandled exception: %s", exc_value)
    logging.log(logging.DEBUG, "Full traceback:", exc_info=(exc_type, exc_value, exc_tb))
    sys.exit(1)

def set_up_logging(log_to_file: bool, app_name: str):
    """
    Set up the loggging system.
    log_to_file: wether to log to a file or not (named <app_name>.log)
    app_name: the name of the current program
    """

    # Set exceptions to be handeled by custom function
    sys.excepthook = handle_uncaught

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Logging handler to log to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(stdout_handler)

    # Optionally set up logging to a file
    if log_to_file:
        file_handler = logging.FileHandler(app_name+".log", mode="a", encoding="utf-8")
        file_handler.setFormatter(CustomFormatter(use_color=False))
        root_logger.addHandler(file_handler)

    # On linux, try to set up logging to the systemd journal
    if platform.system() == "Linux":
        try:
            from systemd.journal import JournalHandler

            journal_handler = JournalHandler(SYSLOG_IDENTIFIER=app_name)
            root_logger.addHandler(journal_handler)
        except ImportError:
            logging.info("Failed to import python systemd module. Logging to the journal will be disabled. To install journald support, run poetry install with --with journald")
