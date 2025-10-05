import logging
import os
import re
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict

import mariadb
from dash import Dash, html

COLORS = {
    "background": "#121214",
    "text": "#ffffff"
}

class WebApp(ABC):
    def __init__(self, app_name: str, config: Dict[str, Any], db_conn: mariadb.Connection) -> None:
        logging.info("Initializing "+app_name)

        self._app_name = app_name

        self.port = config["port"]
        self.db_conn = db_conn

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
        self.app.logger = logging.getLogger()

    def run(self):
        """Run the website"""

        logging.info("Running "+self._app_name)
        
        # Run dash app
        try:
            self.app.run(host="0.0.0.0", port=self.port)
        except KeyboardInterrupt:
            logging.info("Caught KeyboardInterrupt, shutting down")
        except Exception as e:
            logging.error(f"Got exception while running {self._app_name}: {e}")
            logging.info(traceback.format_exc())
        finally:
            # Close database connection
            if self.db_conn:
                self.db_conn.close()

