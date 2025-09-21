from datetime import datetime
from typing import Dict, List
from collections import defaultdict

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

def get_week_types(cursor: mariadb.Cursor) -> Dict[str, int]:
    """Get sonde type occurences in the past 7 days including today"""

    cursor.execute("""
SELECT
    sonde_type AS value,
    COUNT(*) AS occurrences
FROM meta
WHERE first_rx_time >= CURDATE() - INTERVAL 6 DAY
    AND first_rx_time < CURDATE() + INTERVAL 1 DAY
GROUP BY sonde_type;
""")
    
    data = dict(cursor.fetchall())

    return data

def get_all_types(cursor: mariadb.Cursor) -> Dict[str, int]:
    """Get all time sonde type occurences"""

    cursor.execute("""
SELECT
    sonde_type AS value,
    COUNT(*) AS occurrences
FROM meta
GROUP BY sonde_type;
""")
    
    data = dict(cursor.fetchall())

    return data

def get_week_frame_count(cursor: mariadb.Cursor) -> Dict[datetime, int]:
    """Get average frame count for the past 7 days including today"""

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
    COALESCE(ROUND(AVG(t.frame_count), 0), 0 ) AS avg_val
FROM
    dates
    LEFT JOIN meta AS t
        ON DATE(t.first_rx_time) = dates.d
GROUP BY
  dates.d
ORDER BY
  dates.d;
""")
    
    data = dict(cursor.fetchall())

    return data

def get_week_burst_alts(cursor: mariadb.Cursor) -> Dict[datetime, List[int]]:
    """Get a list of burst altitudes for the past 7 days including today"""

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
    t.burst_alt 
FROM
    dates
    LEFT JOIN meta AS t
        ON DATE(t.first_rx_time) = dates.d
        AND t.frame_count IS NOT NULL
ORDER BY
    dates.d, 
    t.first_rx_time;
""")

    data = cursor.fetchall()
    
    grouped = defaultdict(list)
    for d, value in data:
        grouped[d].append(value)

    grouped = dict(grouped)

    return grouped
