import os, logging
from typing import List, Tuple

def read_launchsites() -> List[Tuple[str, float, float]]:
    """Read the launchsites file in the current directory and return list of name, lat and lon"""

    if not os.path.isfile("launchsites.txt"):
        logging.warning("Couldn't find launchsites.txt in current directory")
        return []
    
    try:
        with open("launchsites.txt", "r") as f:
            lines = f.readlines()

        results = []
        for line in lines:
            if len(line) < 5: # Skip empty/invalid lines
                continue

            line = line.strip().split(",")

            name = line[0]
            lat = float(line[1])
            lon = float(line[2])

            results.append((name, lat, lon))

        return results
    except Exception as e:
        logging.error("Got exception while loading launchsites.txt: "+str(e))
        
        return []