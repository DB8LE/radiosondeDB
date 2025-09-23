from . import database

import logging, traceback, os

import mariadb
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

class Map():
    def __init__(self, port: int, connection: mariadb.Connection) -> None:
        logging.info("Initializing map")

        self.port = port
        self.connection = connection

        # Get assets path
        assets_base_path = os.path.join(os.getcwd(), "./assets/")
        assets_bootstrap_path = os.path.join(assets_base_path, "bootstrap.min.css")
        assets_path = os.path.join(assets_base_path, "./map")
        if (not os.path.exists(assets_path)) or (not os.path.exists(assets_bootstrap_path)):
            logging.error(f"Assets path {assets_base_path} or required sub-directories do not exist! \
                          Make sure you're running the program in the right directory.")
            exit(1)

        # Create app
        self.app = Dash(assets_folder=assets_base_path,
                        assets_path_ignore=[r"^(?!map).*$"],
                        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
        self.app.title = "RSDB Map"
        self.app.layout = self._create_page

    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        logging.debug("Creating map")

        # Create cursor
        cursor = self.connection.cursor()

        cursor.close()

        return html.Div(html.H1("Hello, World!"))
    
    def run(self):
        """Run the map"""

        logging.info("Running map")
        
        # Run dash app
        try:
            self.app.run(host="0.0.0.0", port=self.port)
        except Exception as e:
            logging.error(f"Got exception while running map: {e}")
            logging.info(traceback.format_exc())

            # Close cursor
            if self.connection:
                self.connection.close()
