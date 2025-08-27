import json
from datetime import datetime
from typing import Dict, Any, Self

class Packet():
    """
    Class to store a payload_summary type UDP packet from radiosonde_auto_rx.
    Only contains types that have columns in the database.
    Attributes speed and heading are never none if they come from the database.
    Datetime is only none when parsing from UDP message
    """

    def __init__(self):
        self.station: str
        self.serial: str
        self.frame: int
        self.datetime: datetime | None
        self.latitude: float
        self.longitude: float
        self.altitude: int
        self.temperature: float
        self.humidity: float | None = None
        self.pressure: float | None = None
        self.speed: float | None = None
        self.heading: float | None = None
        self.battery: float | None = None
        self.burst_timer: int | None = None
        self.xdata: bytearray | None = None

    def __repr__(self) -> str:
        return f"""
rsdb.Packet:
Station: {self.station}
Serial: {self.serial}
Frame: #{self.frame}
Time: {self.datetime.strftime("%d/%m/%Y %H:%M:%S") if self.datetime is not None else None}
Latitude: {self.latitude}
Longitude: {self.longitude}
Altitude: {self.altitude}m
Temperature: {self.temperature}°C
            """

    def from_dict(self, data_dict: Dict[str, Any]) -> Self | None:
        """
        Generate self from a json decoded payload summary type UDP packet.
        Datetime attribute will be None when parsing via this function, as the UDP packets don't include the date.
        If type is not PAYLOAD_SUMMARY, none is returned. Type key doesn't have to exist.
        """

        # Check if type is payload summary        
        if "type" in data_dict:
            if data_dict["type"] != "PAYLOAD_SUMMARY":
                return None

        # Assign attributes (always present)
        self.station = data_dict["station"]
        self.serial = data_dict["callsign"]
        self.datetime = None
        self.frame = data_dict["frame"]
        self.latitude = data_dict["latitude"]
        self.longitude = data_dict["longitude"]
        self.altitude = data_dict["altitude"]
        self.temperature = data_dict["temp"]
        
        # Assign attributes (optional)
        if "humidity" in data_dict:
            self.humidity = data_dict["humidity"]
        if "pressure" in data_dict:
            self.pressure = data_dict["pressure"]
        if "speed" in data_dict:
            self.speed = data_dict["speed"]
        if "heading" in data_dict:
            self.heading = data_dict["heading"]
        if "batt" in data_dict:
            self.battery = data_dict["batt"]
        if "bt" in data_dict:
            self.burst_timer = data_dict["bt"]
        if "aux" in data_dict:
            self.xdata = data_dict["aux"]

        return self

    def from_json(self, json_data: str | bytes | bytearray) -> Self | None:
        """
        Generate self from either a string, bytes, or bytearray containing a payload summary type UDP packet in json format.
        Datetime attribute will be None when parsing via this function, as the UDP packets don't include the date.
        If type is not PAYLOAD_SUMMARY, none is returned.
        """
        
        data_dict = json.loads(json_data)

        return self.from_dict(data_dict)
