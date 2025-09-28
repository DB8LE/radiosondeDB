import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database, color

import logging, time
from datetime import date
from typing import Dict, Any, List

import folium, mariadb
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State

class Map(rsdb.web.WebApp):
    def __init__(self, app_name: str, config: Dict[str, Any], connection: mariadb.Connection) -> None:
        super().__init__(app_name, config, connection)

        # Set up map update callback
        @self.app.callback(
            [Output("map_iframe", "srcDoc"),
            Output("flight_count", "children")],
            State("input_serial", "value"),
            State("input_min_frames", "value"),
            State("input_date_start", "date"),
            State("input_date_end", "date"),
            Input("button_search", "n_clicks")
        )
        def update_map(serial, min_frame_count, date_start, date_end, n_clicks):
            """Callback to update map"""

            # Only run if user has clicked the button
            if n_clicks > 0:
                cursor = self.db_conn.cursor()

                # Convert date types from string to datetime.date
                if date_start is not None:
                    date_start = date.fromisoformat(date_start)
                if date_end is not None:
                    date_end = date.fromisoformat(date_end)

                # Perform search in DB
                logging.debug("Searching database")
                search_results = rsdb.database.search_sondes(cursor, serial, min_frame_count, date_start, date_end)
                logging.debug(f"Got {len(search_results)} results")

                # Create map
                map_start_time = time.time()
                map = self._make_map(cursor, search_results).get_root().render()
                map_processing_time = time.time() - map_start_time

                cursor.close()

                # Create text for flight count map overlay
                flight_count_text = f"({round(map_processing_time, 1)}s) Showing {len(search_results)} flights"

                return map, flight_count_text
        
        # Prepare inputs
        input_serial = dcc.Input(id="input_serial", type="text", placeholder="Serial", className="w-100", style={"height": "100%"})
        # TODO: seconds received might be better here?
        input_min_frames = dcc.Input(id="input_min_frames", type="number", placeholder="Min. Frames", className="w-100", style={"height": "100%"})
        # FIXME: Date pickers look weird and sometimes don't scale properly, but I can't find a fix
        input_date_start = dcc.DatePickerSingle(id="input_date_start", placeholder="Start Date")
        input_date_end = dcc.DatePickerSingle(id="input_date_end", placeholder="End Date")
        button_search = html.Button("Search", id="button_search", n_clicks=0, className="w-100", style={"height": "100%"})

        # Arrange inputs
        inputs = dbc.Container([
            dbc.Row([
                dbc.Col(input_serial, width=8),
                dbc.Col(input_min_frames, width=1),
                dbc.Col(input_date_start, width=1),
                dbc.Col(input_date_end, width=1),
                dbc.Col(button_search, width=1)
            ], class_name="g-0", style={"height": "5vh"})
        ], style={"width": "100%", "height": "5vh", "flex": "0 0 auto"}, fluid=True)

        # Set app layout
        self.app.layout = html.Div([
            html.Div(inputs, style={"width": "100%"}),
            html.Div([
                html.Iframe(
                    id="map_iframe",
                    srcDoc=folium.Map().get_root().render(),
                    style={"width": "100%", "height": "100%"}
                ),
                html.Div("(0.0s) Showing 0 flights", id="flight_count", className="overlay-text")
            ], style={"flex": "1 1 auto", "overflow": "auto"})
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
                                color=color.get_track_color(),
                                tooltip=serial
                ).add_to(map)
        else:
            map = folium.Map()
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        return map
        