from . import database, graphs

import logging, traceback, os

import mariadb
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
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

        assets_path = os.path.join(os.getcwd(), "./assets/dashboard")
        if not os.path.exists(assets_path):
            logging.error(f"Assets path {assets_path} does not exist! Make sure you're running the program in the right directory.")
            exit(1)

        self.app = Dash(assets_folder=assets_path, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
        self.app.title = "RSDB Dashboard"
        self.app.layout = self._create_page

    def _apply_figure_settings(self, figure: go.Figure, title: str | None = None):
        """Internal function to apply common settings to a plotly figure"""

        figure.update_layout( # Set background
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"]
        )
        figure.update_layout( # Set font and title
            font=dict(
                family="sans-serif",
                size=16,
                color=COLORS["text"]
            )
        )

        if title: # Optionally set title
            figure.update_layout(title=title)

    def _create_figure(self, graph, title: str | None = None) -> go.Figure:
        """Internal function to create a figure for a graph and set some common settings"""

        figure = go.Figure(graph) # Create figure

        self._apply_figure_settings(figure, title)

        return figure

    def _create_page(self) -> html.Div:
        """Internal function to get data from database and assemble the web page"""

        # TODO: Add option for caching dashboard?
        logging.debug("Creating dashboard")

        # Initialize dashboard
        app = Dash(assets_folder="./assets/dashboard")
        app.title = "RSDB Dashboard"

        # Get sonde count
        sonde_count = database.get_sonde_count(self.cursor)

        # Define graphs
        week_sonde_count = graphs.WeekSondeCount(COLORS, self.cursor)
        sonde_types = graphs.SondeTypes(COLORS, self.cursor)
        week_burst_altitudes = graphs.WeekBurstAltitudes(COLORS, self.cursor)
        week_frame_count = graphs.WeekFrameCount(COLORS, self.cursor)

        # TODO: Allow user to configure plots in config file
        # Create layout for graphs with dbcs
        logging.debug("Creating page layout")

        graphs_layout = dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Graph(figure=week_sonde_count.create_figure()), style={"height": "100%"}, width=6),
                dbc.Col(dcc.Graph(figure=sonde_types.create_figure()), width=6)
            ], style={"height": "40vh"}),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=week_burst_altitudes.create_figure()), style={"height": "100%"}),
                dbc.Col(dcc.Graph(figure=week_frame_count.create_figure()), style={"height": "100%"})
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
