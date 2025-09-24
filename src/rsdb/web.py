import logging, os, traceback, re
from abc import ABC, abstractmethod
from typing import Dict, Any

import mariadb
from dash import Dash, html

COLORS = {
    "background": "#121214",
    "text": "#ffffff"
}

class WebApp(ABC):
    def __init__(self, app_name: str, config: Dict[str, Any], connection: mariadb.Connection, set_layout: bool = True) -> None:
        logging.info("Initializing "+app_name)

        self._app_name = app_name

        self.port = config["port"]
        self.connection = connection

        # Get assets path
        assets_base_path = os.path.join(os.getcwd(), "./assets/")
        assets_bootstrap_path = os.path.join(assets_base_path, "bootstrap.min.css")
        assets_path = os.path.join(assets_base_path, app_name)
        if (not os.path.exists(assets_path)) or (not os.path.exists(assets_bootstrap_path)):
            logging.error(f"Assets path {assets_base_path} or required sub-directories do not exist! \
                          Make sure you're running the program in the right directory.")
            exit(1)

        # Create app
        self.app = Dash(assets_folder=assets_base_path,
                        assets_path_ignore=[r"^(?!" + re.escape(app_name) + r").*$"],
                        prevent_initial_callbacks=True,
                        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
        self.app.title = "RSDB "+app_name.capitalize()
        if set_layout:
            self.app.layout = self._create_page

    @abstractmethod
    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        pass
    
    def run(self):
        """Run the website"""

        logging.info("Running "+self._app_name)
        
        # Run dash app
        try:
            self.app.run(host="0.0.0.0", port=self.port)
        except Exception as e:
            logging.error(f"Got exception while running {self._app_name}: {e}")
            logging.info(traceback.format_exc())

            # Close cursor
            if self.connection:
                self.connection.close()

