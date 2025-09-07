import logging
from datetime import datetime
from typing import Dict

import mariadb

def get_sonde_count(cursor: mariadb.Cursor) -> int:
    """Get amount of sondes in the database"""

    cursor.execute("SELECT COUNT(*) FROM meta;")
    
    return cursor.fetchone()[0]

def get_week_sonde_count(cursor: mariadb.Cursor) -> Dict[datetime, int]:
    """Get amount of sondes for the last seven days (including today)"""

    cursor.execute("""
WITH RECURSIVE dates AS (
  SELECT CURDATE() AS d
  UNION ALL
  SELECT d - INTERVAL 1 DAY
  FROM dates
  WHERE d > CURDATE() - INTERVAL 6 DAY
)
SELECT
  dates.d AS day,
  COALESCE(t.cnt, 0) AS row_count
FROM dates
LEFT JOIN (
  SELECT DATE(first_rx_time) AS day, COUNT(*) AS cnt
  FROM meta
  WHERE DATE(first_rx_time) BETWEEN CURDATE() - INTERVAL 6 DAY AND CURDATE()
  GROUP BY DATE(first_rx_time)
) AS t ON t.day = dates.d
ORDER BY day DESC;
""")

    data = dict(cursor.fetchall())

    return data
