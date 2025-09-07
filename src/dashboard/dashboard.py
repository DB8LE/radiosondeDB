from . import database

import logging, traceback

import mariadb
import plotly.graph_objects as go
from dash import Dash, html, dcc

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
        week_sonde_count = database.get_week_sonde_count(self.cursor)

        # Create graphs
        logging.debug("Creating graphs")

        figure = go.Figure([go.Bar(
            x=list(week_sonde_count.keys()),
            y=list(week_sonde_count.values())
        )])
        figure.update_layout( # Set background
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"]
        )
        figure.update_layout( # Set font and title
            font=dict(
                family="sans-serif",
                size=16,
                color=COLORS["text"]
            ),
            title="7 Day Sonde Count"
        )
        
        # Initialize dashboard
        logging.debug("Creating page layout")
        app = Dash(assets_folder="./assets/dashboard")
        app.title = "RSDB Dashboard"

        layout = html.Div(style={"backgroundColor": COLORS["background"], "height": "100vh"}, children=[
            html.H1(children="RSDB Dashboard", style={"color": COLORS["text"]}),

            html.Div(children=f"Total sondes: {sonde_count}", style={
                "color": COLORS["text"],
                "padding-left": "2%",
                "padding-bottom": "1%"}),

            dcc.Graph(figure=figure, style={"width": "95%", "height": "80%", "padding-left": "2%"})
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
