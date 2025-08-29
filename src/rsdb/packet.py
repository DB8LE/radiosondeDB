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
        self.type: str | None
        self.subtype: str | None
        self.frequency: float | None
        self.frame: int
        self.time_str: str
        self.datetime: datetime | None
        self.latitude: float
        self.longitude: float
        self.altitude: int
        self.temperature: float | None = None
        self.humidity: float | None = None
        self.pressure: float | None = None
        self.speed: float | None = None
        self.battery: float | None = None
        self.burst_timer: int | None = None
        self.xdata: bytearray | None = None
        self.rs41_mainboard: str | None = None
        self.rs41_mainboard_fw: str | None = None

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
        self.time_str = data_dict["time"]
        self.datetime = None
        self.frame = data_dict["frame"]
        self.latitude = data_dict["latitude"]
        self.longitude = data_dict["longitude"]
        self.altitude = data_dict["altitude"]
        
        # Assign optional attributes and set placeholder values to none
        if "model" in data_dict:
            self.type = data_dict["model"]
        if "subtype" in data_dict:
            self.subtype = data_dict["subtype"]
        if "freq" in data_dict:
            self.frequency = round(float(data_dict["freq"][:-4]), 2)
        if "temp" in data_dict:
            self.temperature = data_dict["temp"]
            if int(self.temperature) == 273: self.temperature = None # type: ignore
        if "humidity" in data_dict:
            self.humidity = data_dict["humidity"]
            if int(self.humidity) == -1: self.humidity = None # type: ignore
        if "pressure" in data_dict:
            self.pressure = data_dict["pressure"]
            if int(self.pressure) == -1: self.pressure = None # type: ignore
        if "speed" in data_dict:
            self.speed = data_dict["speed"]
        if "batt" in data_dict:
            self.battery = data_dict["batt"]
        if "bt" in data_dict:
            self.burst_timer = data_dict["bt"]
            if self.burst_timer == 66535: self.burst_timer = None
        if "aux" in data_dict:
            self.xdata = data_dict["aux"]
        if "rs41_mainboard" in data_dict:
            self.rs41_mainboard = data_dict["rs41_mainboard"]
        if "rs41_mainboard_fw" in data_dict:
            self.rs41_mainboard_fw = data_dict["rs41_mainboard_fw"]

        return self

    def from_json(self, json_data: str | bytes | bytearray) -> Self | None:
        """
        Generate self from either a string, bytes, or bytearray containing a payload summary type UDP packet in json format.
        Datetime attribute will be None when parsing via this function, as the UDP packets don't include the date.
        If type is not PAYLOAD_SUMMARY, none is returned.
        """
        
        data_dict = json.loads(json_data)

        return self.from_dict(data_dict)
