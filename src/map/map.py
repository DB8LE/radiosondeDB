import src.rsdb as rsdb
from . import database

import logging

import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

class Map(rsdb.web.WebApp):
    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        logging.debug("Creating map")

        # Create cursor
        cursor = self.connection.cursor()

        

        cursor.close()

        return html.Div(html.H1("Hello, World!"))
