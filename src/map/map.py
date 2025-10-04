import src.rsdb as rsdb
from src.rsdb.web import COLORS
from . import database, color, launchsites

import logging, time, copy
from datetime import date
from typing import Dict, Any, List

import folium, mariadb
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State

class Map(rsdb.web.WebApp):
    def __init__(self, app_name: str, config: Dict[str, Any], connection: mariadb.Connection) -> None:
        super().__init__(app_name, config, connection)

        # Read launchsites
        self.launchsites = launchsites.read_launchsites()

        # Create empty map with launchsites plotted
        self.empty_map = folium.Map()
        for launchsite in self.launchsites:
            folium.CircleMarker(
                location=(launchsite[1], launchsite[2]),
                radius=6,
                color="black",
                weight=2,
                fill=True,
                fill_opacity=0.1,
                opacity=1,
                tooltip=launchsite[0]
            ).add_to(self.empty_map)

        # Set up map update callback
        @self.app.callback(
            [Output("map_iframe", "srcDoc"),
            Output("flight_count", "children")],
            State("input_serial", "value"),
            State("input_types", "value"),
            State("input_min_frames", "value"),
            State("input_date_start", "date"),
            State("input_date_end", "date"),
            Input("button_search", "n_clicks")
        )
        def update_map(serial, types, min_frame_count, date_start, date_end, n_clicks):
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
                search_results = rsdb.database.search_sondes(cursor, serial, types, min_frame_count, date_start, date_end)
                logging.debug(f"Got {len(search_results)} results")

                # Create map
                map_start_time = time.time()
                map = self._make_map(cursor, search_results).get_root().render()
                map_processing_time = time.time() - map_start_time

                cursor.close()

                # Create text for flight count map overlay
                flight_count_text = f"({round(map_processing_time, 1)}s) Showing {len(search_results)} flights"

                return map, flight_count_text
            
        # Get available types from DB
        # TODO: this should update every once in a while without having to restart
        cursor = self.db_conn.cursor()
        available_sonde_types = database.get_sonde_types(cursor)
        cursor.close()

        # Prepare inputs
        input_serial = dcc.Input(id="input_serial",
                                 type="text",
                                 placeholder="Serial",
                                 className="w-100",
                                 style={"height": "100%"})
        # FIXME: This doesnt scale properly on small heights
        input_types = dcc.Dropdown(id="input_types",
                                   options=available_sonde_types,
                                   multi=True,
                                   searchable=False,
                                   className="w-100",
                                   style={"height": "5vh"}) # This refuses to scale with 100% height
        # TODO: seconds received might be better here?
        input_min_frames = dcc.Input(id="input_min_frames",
                                     type="number",
                                     placeholder="Min. Frames",
                                     className="w-100",
                                     style={"height": "100%"})
        # FIXME: Date pickers don't scale properly on small heights either
        input_date_start = dcc.DatePickerSingle(id="input_date_start",
                                                display_format="Y-M-D",
                                                placeholder="Start Date")
        input_date_end = dcc.DatePickerSingle(id="input_date_end",
                                              display_format="Y-M-D",
                                              placeholder="End Date")
        button_search = html.Button("Search",
                                    id="button_search",
                                    n_clicks=0,
                                    className="w-100",
                                    style={"height": "100%"})

        # Arrange inputs
        inputs = dbc.Container([
            dbc.Row([
                dbc.Col(input_serial, width=6),
                dbc.Col(input_types, width=2, style={"height": "5vh"}),
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
        
    def _make_map(self, cursor: mariadb.Cursor, serials: List[str]):
        """Generate the map with data from the database"""

        logging.debug("Creating map")

        # Get flight paths from DB
        logging.debug("Getting data from DB")
        start = time.time()
        flight_paths = database.get_flight_paths(cursor, serials)
        flights_meta = database.get_flight_meta(cursor, serials)
        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        # Create map
        logging.debug("Drawing map")
        start = time.time()
        map = copy.deepcopy(self.empty_map)
        for serial, flight_path in flight_paths.items():
            flight_color=color.get_track_color()

            # Add flight line
            folium.PolyLine(flight_path,
                            color=flight_color,
                            tooltip=serial
            ).add_to(map)

            # Add dots for first receive and last receive
            meta = flights_meta[serial]
            first_rx = meta[0]
            last_rx = meta[1]
            burst = meta[2]

            folium.CircleMarker(
                location=(first_rx[1], first_rx[2]),
                radius=3,
                color=flight_color,
                weight=3,
                fill=True,
                fill_opacity=1,
                opacity=1,
                tooltip=f"first receive @ {first_rx[3]}m on {first_rx[0].strftime("%Y-%m-%d %H:%M:%S")}"
            ).add_to(map)

            folium.CircleMarker(
                location=(last_rx[1], last_rx[2]),
                radius=3,
                color=flight_color,
                weight=3,
                fill=True,
                fill_opacity=1,
                opacity=1,
                tooltip=f"last receive @ {last_rx[3]}m on {last_rx[0].strftime("%Y-%m-%d %H:%M:%S")}"
            ).add_to(map)

            if burst is not None:
                folium.CircleMarker(
                    location=(burst[1], burst[2]),
                    radius=4,
                    color=flight_color,
                    weight=3,
                    fill=True,
                    fill_opacity=1,
                    opacity=1,
                    tooltip=f"last receive @ {burst[3]}m on {burst[0].strftime("%Y-%m-%d %H:%M:%S")}"
                ).add_to(map)

        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        return map
        