import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database

import logging, time
from typing import Dict, Any, List

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
        flight_paths = []
        for serial in serials:
            flight_path = database.get_flight_path(cursor, serial)

            if flight_path == []:
                logging.error(f"Sonde {serial} has a meta table entry but none in tracking table.")
            else:
                flight_paths.append(flight_path)
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        # Create map
        logging.debug("Drawing map")
        start = time.time()
        if flight_paths != []:
            map = folium.Map()
            for flight_path in flight_paths:
                folium.PolyLine(flight_path).add_to(map)
        else:
            map = folium.Map()
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        return map
        