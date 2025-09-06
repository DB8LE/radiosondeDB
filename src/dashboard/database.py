import logging

import mariadb

def get_sonde_count(cursor: mariadb.Cursor) -> int:
    """Get amount of sondes in the database"""

    cursor.execute("SELECT COUNT(*) FROM meta;")
    
    return cursor.fetchone()[0]
