from . import database

import logging, traceback

import mariadb
from dash import Dash, html

COLORS = {
    "background": "#121214",
    "text": "#ffffff"
}

class Dashboard:
    def __init__(self, port: int, cursor: mariadb.Cursor) -> None:
        logging.info("Initializing dashboard")

        self.port = port
        self.cursor = cursor

        self.app = Dash(assets_folder="./assets/dashboard")
        self.app.title = "RSDB Dashboard"
        self.app.layout = self._create_page

    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        logging.debug("Creating page")

        # Get data from MariaDB
        logging.debug("Fetching data from MariaDB")

        sonde_count = database.get_sonde_count(self.cursor)

        # Initialize dashboard
        logging.debug("Creating page layout")
        app = Dash(assets_folder="./assets/dashboard")
        app.title = "RSDB Dashboard"

        layout = html.Div(style={"backgroundColor": COLORS["background"], "height": "100vh"}, id="main-div", children=[
            html.H1(children="RSDB Dashboard", style={"color": COLORS["text"]}),

            html.Div(children=f"Total sondes: {sonde_count}", style={"color": COLORS["text"]})
        ])

        return layout

    def run(self):
        """Run the dashboard"""

        logging.info("Running dashboard")
        
        # Run dash app
        try:
            self.app.run(host="0.0.0.0", port=self.port)
        except Exception as e:
            logging.error(f"Got exception while running dashboard: {e}")
            logging.info(traceback.format_exc())

            # Close cursor
            if self.cursor:
                self.cursor.close()
