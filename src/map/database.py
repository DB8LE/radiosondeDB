from collections import defaultdict
from typing import Dict, List, Tuple

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
