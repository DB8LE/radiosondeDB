import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database

import logging, time, random
from typing import Dict, Any, List

import folium, mariadb
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State

SONDE_TRACK_COLORS = [
    '#4FC3F7', '#29B6F6', '#03A9F4', '#039BE5', '#0288D1',
    '#0277BD', '#01579B', '#26C6DA', '#00BCD4', '#00ACC1',
    '#0097A7', '#00838F', "#0E979B", '#1976D2', '#1565C0',
    '#BA68C8', '#AB47BC', '#9C27B0', '#8E24AA', '#7B1FA2',
    '#6A1B9A', "#5A20A1", '#7E57C2', '#673AB7', '#5E35B1',
    '#F06292', '#EC407A', '#E91E63', '#D81B60', '#C2185B',
    '#AD1457', '#880E4F', '#FF6F94', '#F45C82', '#E84A6F',
    '#FFD54F', '#FFCA28', '#FFC107', '#FFB300', '#FFA000',
    '#FF8F00', '#FF6F00', '#FF8A65', '#FF7043', '#F4511E'
]
COLOR_MAX_CHANGE = 20 # Maximum amount to change the sonde track colors by

def get_track_color() -> str:
    """Get a color for a sonde track"""

    # Pick random color, remove # and convert to RGB
    hex_color = random.choice(SONDE_TRACK_COLORS)[-6:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Apply small random change to each value
    new_r = max(0, min(255, r + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    new_g = max(0, min(255, g + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    new_b = max(0, min(255, b + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    
    # Convert back to hex
    return f"#{new_r:02x}{new_g:02x}{new_b:02x}"

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

            # Only run if user has clicked the button
            if n_clicks > 0:
                cursor = self.db_conn.cursor()

                # Perform search in DB
                logging.debug("Searching database")
                search_results = rsdb.database.search_sondes(cursor, serial)
                logging.debug(f"Got {len(search_results)} results")

                # Create map
                map = self._make_map(cursor, search_results).get_root().render()

                cursor.close()

                return map
        
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
                srcDoc=folium.Map().get_root().render(),
                style={"flex": "1 1 auto", "overflow": "auto"}
            )
        ], style={"height": "100vh", "display": "flex", "flexDirection": "column"})
        
    def _make_map(self, cursor: mariadb.Cursor, serials: List[str] = []):
        """Generate the map with data from the database"""

        logging.debug("Creating map")

        # Get flight paths from DB
        logging.debug("Getting data from DB")
        start = time.time()
        flight_paths = {}
        for serial in serials:
            flight_path = database.get_flight_path(cursor, serial)

            if flight_path == []:
                logging.error(f"Sonde {serial} has a meta table entry but none in tracking table.")
            else:
                flight_paths[serial] = flight_path
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        # Create map
        logging.debug("Drawing map")
        start = time.time()
        if flight_paths != []:
            map = folium.Map()
            for serial, flight_path in flight_paths.items():
                folium.PolyLine(flight_path,
                                color=get_track_color(),
                                tooltip=serial
                ).add_to(map)
        else:
            map = folium.Map()
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        return map
        