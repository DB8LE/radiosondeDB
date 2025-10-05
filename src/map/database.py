from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import mariadb


def get_flight_paths(cursor: mariadb.Cursor, serials: List[str]) -> Dict[str, List[Tuple[float, float]]]:
    """
    Get lat/longs for flight paths of a list of sondes.
    Returns a dict with serial as key and list of lat/longs as value.
    """

    # Get raw data from DB in one big query
    placeholders = ", ".join(["?"] * len(serials))
    cursor.execute(f"SELECT serial, latitude, longitude FROM tracking \
                     WHERE serial IN ({placeholders})", serials) # Should this be ordered?

    results = cursor.fetchall()

    # Format data into dict
    data = defaultdict(list)
    for result in results:
        data[result[0]].append((float(result[1]), float(result[2])))

    return data

metas_point = Tuple[datetime, float, float, int]
metas_type = Dict[str, Tuple[metas_point, metas_point, Optional[metas_point]]]
def get_flight_meta(cursor: mariadb.Cursor, serials: List[str]) -> metas_type:
    """
    Get first receive, burst and last receive points for flight paths of a list of sondes.
    Returns a dict with serial as key and tuple of points first, last and if available burst,
    with each point containing time, latitude, longitude and altitude
    """

    # Get raw data from DB in one big query
    placeholders = ", ".join(["?"] * len(serials))
    cursor.execute(f"SELECT serial, \
                            first_rx_time, first_rx_lat, first_rx_lon, first_rx_alt, \
                            last_rx_time, last_rx_lat, last_rx_lon, last_rx_alt, \
                            burst_time, burst_lat, burst_lon, burst_alt FROM meta \
                    WHERE serial IN ({placeholders})", serials)

    results = cursor.fetchall()

    # Format data correctly
    data = {}
    for result in results:
        burst = None if result[9] is None else (result[9], result[10], result[11], result[12])

        data[result[0]] = (
            (result[1], result[2], result[3], result[4]),
            (result[5], result[6], result[7], result[8]),
            burst
        )

    return data
        

def get_sonde_types(cursor: mariadb.Cursor) -> List[str]:
    """Get a list of sonde types available in database"""

    cursor.execute("SELECT DISTINCT sonde_type FROM meta;")

    results = cursor.fetchall()

    return [sonde_type[0] for sonde_type in results]
