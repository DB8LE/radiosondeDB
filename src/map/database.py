from typing import List, Tuple

import mariadb

def get_flight_path(cursor: mariadb.Cursor, serial: str) -> List[Tuple[float, float] | None]:
    """Get flight path in latitude/longitude coordinates for a particular sonde serial. Returns none if no results."""

    cursor.execute("SELECT latitude, longitude FROM tracking WHERE serial = ?;", (serial,))

    return cursor.fetchall()
