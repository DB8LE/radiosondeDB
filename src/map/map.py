import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database

import logging
from typing import Dict, Any

import folium, mariadb
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State

class Map(rsdb.web.WebApp):
    def __init__(self, app_name: str, config: Dict[str, Any], connection: mariadb.Connection) -> None:
        super().__init__(app_name, config, connection)

        # Set up map update callback
        @self.app.callback(
            Output("map_iframe", "srcDoc"),
            State("input_serial", "value"),
            Input("button_search", "n_clicks")
        )
        def update_map(serial, n_clicks):
            """Callback to update map"""

            return self._make_map(serial).get_root().render()
        
        # Prepare inputs
        input_serial = dcc.Input(id="input_serial", type="text", placeholder="Serial", className="w-100", style={"height": "100%"})
        button_search = html.Button("Search", id="button_search", n_clicks=0, className="w-100", style={"height": "100%"})

        # Arrange inputs
        inputs = dbc.Container([
            dbc.Row([
                dbc.Col(input_serial, width=11),
                dbc.Col(button_search, width=1)
            ], class_name="g-0", style={"height": "5vh"})
        ], style={"width": "100%", "height": "5vh", "flex": "0 0 auto"}, fluid=True)

        # Set app layout
        self.app.layout = html.Div([
            html.Div(inputs, style={"width": "100%"}),
            html.Iframe(
                id="map_iframe",
                srcDoc=self._make_map().get_root().render(),
                style={"flex": "1 1 auto", "overflow": "auto"}
            )
        ], style={"height": "100vh", "display": "flex", "flexDirection": "column"})
        
    def _make_map(self, serial: str = ""):
        """Generate the map with data from the database"""

        logging.debug("Creating map")

        # Make DB query
        cursor = self.connection.cursor()
        flight_path = database.get_flight_path(cursor, serial)
        cursor.close()

        # Create map
        if flight_path != []:
            map = folium.Map(location=flight_path[round(len(flight_path)/2)], zoom_start=7) # center on middle flight point
            folium.PolyLine(flight_path).add_to(map)
        else:
            map = folium.Map()

        return map
        