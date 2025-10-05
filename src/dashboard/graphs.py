from abc import ABC, abstractmethod
from typing import Any, Dict

import mariadb
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import database


# Base graph class
class DashboardGraph(ABC):
    def __init__(self, COLORS: Dict[str, str], cursor: mariadb.Cursor) -> None:
        self.COLORS = COLORS
        self.cursor = cursor

    def _apply_figure_settings(self, figure: go.Figure, title: str | None = None):
        """Internal function to apply common settings to a plotly figure"""

        figure.update_layout( # Set background
            paper_bgcolor=self.COLORS["background"],
            plot_bgcolor=self.COLORS["background"]
        )
        figure.update_layout( # Set font and title
            font=dict(
                family="sans-serif",
                size=16,
                color=self.COLORS["text"]
            ),
            margin=dict(b=0)
        )

        if title: # Optionally set title
            figure.update_layout(title=title)

    def _make_figure(self, graph, title: str | None = None) -> go.Figure:
        """Internal function to create a figure for a graph and set some common settings"""

        figure = go.Figure(graph) # Create figure

        self._apply_figure_settings(figure, title)

        return figure

    @abstractmethod
    def create_figure(self) -> go.Figure:
        """Create a plotly figure for this graph class"""

        pass
    

# Child graph classes

class WeekSondeCount(DashboardGraph):
    def create_figure(self) -> go.Figure:
        data = database.get_week_sonde_count(self.cursor)

        figure = self._make_figure(go.Bar(
            x=list(data.keys()),
            y=list(data.values())
        ), "Sonde Count (7d)")

        return figure

class SondeTypes(DashboardGraph):
    def create_figure(self) -> go.Figure:
        data_week = database.get_week_types(self.cursor)
        data_all = database.get_all_types(self.cursor)

        # FIXME:  title is a bit lower than other graphs
        # Create subplot
        figure = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]])

        # Add pie charts
        figure.add_trace(
            go.Pie(
            labels=list(data_week.keys()),
            values=list(data_week.values())),
            row=1, col=1
        )

        figure.add_trace(
            go.Pie(
            labels=list(data_all.keys()),
            values=list(data_all.values())),
            row=1, col=2
        )

        # Make figure
        self._apply_figure_settings(figure, "Sonde Type (7d/all)")
        figure.update_layout(margin=dict(b=30))

        return figure
    
class WeekBurstAltitudes(DashboardGraph):
    def create_figure(self) -> go.Figure:
        data = database.get_week_burst_alts(self.cursor)

        # Create box graphs
        box_graphs = []
        for day, altitudes in data.items():
            box_graphs.append(go.Box(
                y=altitudes,
                name=str(day)
            ))

        # Make figure
        figure = self._make_figure(box_graphs, "Burst Altitude (7d)")
        figure.update_layout(showlegend=False)

        return figure
    
class WeekFrameCount(DashboardGraph):
    def create_figure(self) -> go.Figure:
        data = database.get_week_frame_count(self.cursor)
    
        figure = self._make_figure(go.Scatter( # TODO: maybe add second line/y-axis with time instead of frames?
            x=list(data.keys()),
            y=list(data.values())
        ), title="Daily Avg. Frame Count (7d)")

        return figure
