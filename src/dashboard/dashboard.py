import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database, graphs

import logging, traceback, os
from typing import Dict, Any

import mariadb
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

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

class Dashboard(rsdb.web.WebApp):
    def __init__(self, app_name: str, config: Dict[str, Any], connection: mariadb.Connection) -> None:
        super().__init__(app_name, config, connection, False)

        self.top_left_graph = config["top_left_graph"]
        self.top_right_graph = config["top_right_graph"]
        self.bottom_left_graph = config["bottom_left_graph"]
        self.bottom_right_graph = config["bottom_right_graph"]
        
        # Ensure create_page is only called for the first time once variables have been set
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
                dbc.Col(dcc.Graph(figure=top_right_graph.create_figure()), style={"height": "100%"}, width=6)
            ], style={"height": "40vh"}),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=bottom_left_graph.create_figure()), style={"height": "100%"}, width=6),
                dbc.Col(dcc.Graph(figure=bottom_right_graph.create_figure()), style={"height": "100%"}, width=6)
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
