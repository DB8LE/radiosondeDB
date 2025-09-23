from . import database, graphs

import logging, traceback, os
from typing import Dict, Any

import mariadb
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

COLORS = {
    "background": "#121214",
    "text": "#ffffff"
}

def get_graph_from_name(graph_name: str, cursor: mariadb.Cursor) -> graphs.DashboardGraph:
    """Get a graph class from a graph name. Requires a cursor to initialize the graph class with."""

    if graph_name == "week_sonde_count":
        return graphs.WeekSondeCount(COLORS, cursor)
    elif graph_name == "sonde_types":
        return graphs.SondeTypes(COLORS, cursor)
    elif graph_name == "week_burst_altitudes":
        return graphs.WeekBurstAltitudes(COLORS, cursor)
    elif graph_name == "week_frame_count":
        return graphs.WeekFrameCount(COLORS, cursor)
    else:
        logging.error(f"Attemped to get class for invalid name {graph_name}")
        exit(1)

class Dashboard:
    def __init__(self, dashboard_config: Dict[str, Any], connection: mariadb.Connection) -> None:
        logging.info("Initializing dashboard")

        self.port = dashboard_config["port"]
        self.connection = connection

        self.top_left_graph = dashboard_config["top_left_graph"]
        self.top_right_graph = dashboard_config["top_right_graph"]
        self.bottom_left_graph = dashboard_config["bottom_left_graph"]
        self.bottom_right_graph = dashboard_config["bottom_right_graph"]

        # Load assets
        assets_path = os.path.join(os.getcwd(), "./assets/dashboard")
        if not os.path.exists(assets_path):
            logging.error(f"Assets path {assets_path} does not exist! Make sure you're running the program in the right directory.")
            exit(1)

        # Create app
        self.app = Dash(assets_folder=assets_path, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
        self.app.title = "RSDB Dashboard"
        self.app.layout = self._create_page

    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        # TODO: Add option for caching dashboard?
        logging.debug("Creating dashboard")

        # Create cursor
        cursor = self.connection.cursor()

        # Get sonde count
        sonde_count = database.get_sonde_count(cursor)

        # Define graphs
        top_left_graph = get_graph_from_name(self.top_left_graph, cursor)
        top_right_graph = get_graph_from_name(self.top_right_graph, cursor)
        bottom_left_graph = get_graph_from_name(self.bottom_left_graph, cursor)
        bottom_right_graph = get_graph_from_name(self.bottom_right_graph, cursor)

        # TODO: Allow user to configure plots in config file
        # Create layout for graphs with dbcs
        logging.debug("Creating page layout")

        graphs_layout = dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Graph(figure=top_left_graph.create_figure()), style={"height": "100%"}, width=6),
                dbc.Col(dcc.Graph(figure=top_right_graph.create_figure()), width=6)
            ], style={"height": "40vh"}),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=bottom_left_graph.create_figure()), style={"height": "100%"}),
                dbc.Col(dcc.Graph(figure=bottom_right_graph.create_figure()), style={"height": "100%"})
            ], style={"height": "40vh"})
        ], fluid=True)

        # Create page layout
        layout = html.Div(style={"backgroundColor": COLORS["background"], "height": "100vh"}, children=[
            html.H1(children="RSDB Dashboard", style={"color": COLORS["text"]}),

            html.Div(children=f"Total sondes: {sonde_count}", style={
                "color": COLORS["text"],
                "font-size": "1.5rem",
                "padding-left": "2%"}),

            html.Div(children=graphs_layout, style={"overflowY": "auto"})
        ])

        cursor.close()

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
            if self.connection:
                self.connection.close()
