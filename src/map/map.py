import copy
import hashlib
import logging
import os
import requests
import socket
import time
from datetime import date
from typing import Any, Dict, List, Tuple, Literal

import dash_bootstrap_components as dbc
import folium
import mariadb
from dash import Input, Output, State, dcc, html

import src.rsdb as rsdb
from src.rsdb.web import COLORS

from . import color, database, launchsites

# Silence requests debug logs
logging.getLogger("urllib3").setLevel(logging.WARNING)

CONNECTION_CHECK_HOSTNAME = "one.one.one.one"
def is_connected() -> bool:
    """Check if there is a working internet connection"""

    try:
        # Check if DNS is reachable
        host = socket.gethostbyname(CONNECTION_CHECK_HOSTNAME)

        # Try to connect to host
        s = socket.create_connection((host, 80), 2)
        s.close()

        return True
    except Exception:
        return False

class Map(rsdb.web.WebApp):
    def __init__(self, app_name: str,
                 map_config: Dict[str, Any],
                 maptiles_config: Dict[str, Any],
                 connection: mariadb.Connection) -> None:
        super().__init__(app_name, map_config, connection)

        self.poi_max_results = map_config["poi_max_results"]

        # Read launchsites
        self.launchsites = launchsites.read_launchsites()

        # Create empty map
        tiles = folium.TileLayer(tiles=maptiles_config["url"],
                                 attr=maptiles_config["attribution"],
                                 min_zoom=maptiles_config["min_zoom"],
                                 max_zoom=maptiles_config["max_zoom"])
        self.empty_map = folium.Map(tiles=tiles)
        
        # If enabled, cache folium dependencies
        if map_config["download_dependencies"] == True:
            self._cache_folium_dependencies(self.empty_map)

        # Create copy of empty map with launchsites
        self.launchsites_map = copy.deepcopy(self.empty_map)
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
            ).add_to(self.launchsites_map)

        # Set up map update callback
        @self.app.callback(
            [Output("map_iframe", "srcDoc"),
            Output("flight_count", "children")],
            State("input_serial", "value"),
            State("input_data_fields", "value"),
            State("input_types", "value"),
            State("input_min_frames", "value"),
            State("input_date_start", "date"),
            State("input_date_end", "date"),
            Input("button_search", "n_clicks")
        )
        def update_map(serial,
                       data_fields,
                       types,
                       min_frame_count,
                       date_start, 
                       date_end, 
                       n_clicks):
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
                map_start_time = time.time()
                search_results = rsdb.database.search_sondes(
                        cursor,
                        serial,
                        data_fields,
                        types,
                        min_frame_count,
                        date_start,
                        date_end
                )
                logging.debug(f"Got {len(search_results)} results")

                # If there are results, create map. If not, return empty map;
                if len(search_results) > 0:
                    # Create map
                    map = self._make_map(cursor, search_results)
                else:
                    map = self.empty_map
                map_processing_time = time.time() - map_start_time
                cursor.close()

                # Create text for flight count map overlay
                flight_count_text = f"({round(map_processing_time, 1)}s) Showing {len(search_results)} flights"

                return map.get_root().render(), flight_count_text
            
        # Get available types from DB
        # TODO: this should update every once in a while without having to restart
        cursor = self.db_conn.cursor()
        available_sonde_types = database.get_sonde_types(cursor)
        cursor.close()

        # Prepare inputs
        input_serial = dcc.Input(
            id="input_serial",
            type="text",
            placeholder="Serial",
            className="w-100",
            style={"height": "100%"}
        )
        
        # FIXME: Dropdowns don't scale properly on small heights
        data_field_options = ["humidity", "pressure", "XDATA"]
        input_data_fields = dcc.Dropdown(
            id="input_data_fields",
            options=data_field_options,
            placeholder="Data Fields",
            multi=True,
            searchable=False,
            className="w-100",
            style={"height": "5vh"}
        ) # This refuses to scale with 100% height

        input_types = dcc.Dropdown(
            id="input_types",
            options=available_sonde_types,
            placeholder="Sonde Types",
            multi=True,
            searchable=False,
            className="w-100",
            style={"height": "5vh"}
        ) # This refuses to scale with 100% height

        # TODO: seconds received might be better here?
        input_min_frames = dcc.Input(
            id="input_min_frames",
            type="number",
            placeholder="Min. Frames",
            className="w-100",
            style={"height": "100%"}
        )

        # FIXME: Date pickers don't scale properly on small heights either
        input_date_start = dcc.DatePickerSingle(
            id="input_date_start",
            display_format="Y-M-D",
            placeholder="Start Date"
        )

        input_date_end = dcc.DatePickerSingle(
            id="input_date_end",
            display_format="Y-M-D",
            placeholder="End Date"
        )

        button_search = html.Button(
            "Search",
            id="button_search",
            n_clicks=0,
            className="w-100",
            style={"height": "100%"}
        )

        # Arrange inputs
        inputs = dbc.Container([
            dbc.Row([
                dbc.Col(input_serial, width=4),
                dbc.Col(input_data_fields, width=2, style={"height": "5vh"}),
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
                    srcDoc=self.empty_map.get_root().render(),
                    style={"width": "100%", "height": "100%"}
                ),
                html.Div("(0.0s) Showing 0 flights", id="flight_count", className="overlay-text")
            ], style={"flex": "1 1 auto", "overflow": "auto"})
        ], style={"height": "100vh", "display": "flex", "flexDirection": "column"})
        
    def _cache_folium_dependencies(self, map: folium.Map):
        """Download required js and css dependencies of a folium map to local storage"""

        logging.info("Caching folium dependencies")

        # Ensure library path exists
        lib_path = os.path.join(os.getcwd(), "./assets/map/lib")
        os.makedirs(lib_path, exist_ok=True)

        # Check for internet connection
        if not is_connected():
            logging.warning("No internet connection. Can't check folium dependencies.")
            return

        # Attempt to download dependencies
        dependency_filenames = []
        def _download_deps(dependencies: List[Tuple[str, str]], dep_type: Literal["js", "css"]):
            for name, url in dependencies:
                filename = url.split("/")[-1]

                # Download file
                try:
                    request = requests.get(url)
                    request.raise_for_status()
                except (requests.Timeout, requests.HTTPError) as e:
                    logging.warning(f"Failed to download folium dependency {name}: {e}")
                    continue

                # Add hash to filename to redownload if changes happened to content but not name
                file_hash = hashlib.sha256(request.content).hexdigest()
                filename = file_hash+"-"+filename
                dependency_filenames.append(filename)
                dependency_path = os.path.join(lib_path, filename)

                # Check if dependency is already downloaded
                if os.path.exists(dependency_path):
                    logging.debug(f"Folium dependency {name} is already downloaded")
                else:
                    # Write file
                    with open(dependency_path, "wb") as f:
                        f.write(request.content)

                # Add file location to map
                short_dependency_path = os.path.join("/assets/map/lib", filename)
                if dep_type == "js":
                    map.add_js_link(name, short_dependency_path)
                else:
                    map.add_css_link(name, short_dependency_path)

                logging.debug(f"Downloaded folium dependency {name}")
        
        _download_deps(map.default_js, "js")
        _download_deps(map.default_css, "css")

        # Delete dependencies that are no longer required
        lib_files = os.listdir(lib_path)
        old_files = list(set(lib_files) - set(dependency_filenames))

        if len(old_files) == 0:
            logging.debug("No extra folium depencies that need to be removed")
            return
        
        logging.debug(f"Removing old files in dependency folder: {old_files}")
        for file in old_files:
            path = os.path.join(lib_path, file)
            os.remove(path)

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
        map = copy.deepcopy(self.launchsites_map)
        skip_poi_dots = len(serials) >= self.poi_max_results
        for serial, flight_path in flight_paths.items():
            flight_color=color.get_track_color()

            # Add flight line
            folium.PolyLine(flight_path,
                            color=flight_color,
                            tooltip=serial
            ).add_to(map)

            # Skip plotting the POI dots if there are too many results
            if skip_poi_dots:
                continue

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
                tooltip=f"first receive @ {first_rx[3]}m on {first_rx[0].strftime('%Y-%m-%d %H:%M:%S')}"
            ).add_to(map)

            folium.CircleMarker(
                location=(last_rx[1], last_rx[2]),
                radius=3,
                color=flight_color,
                weight=3,
                fill=True,
                fill_opacity=1,
                opacity=1,
                tooltip=f"last receive @ {last_rx[3]}m on {last_rx[0].strftime('%Y-%m-%d %H:%M:%S')}"
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
                    tooltip=f"burst @ {burst[3]}m on {burst[0].strftime('%Y-%m-%d %H:%M:%S')}"
                ).add_to(map)
        
        # Automatically zoom to fit all elements
        folium.FitOverlays(max_zoom=8).add_to(map)

        logging.debug(f"Done in {round(time.time()-start, 2)}s")

        return map
        