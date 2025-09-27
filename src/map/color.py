import random

SONDE_TRACK_COLORS = [
    '#4FC3F7', '#29B6F6', '#03A9F4', '#039BE5', '#0288D1',
    '#0277BD', '#01579B', '#26C6DA', '#00BCD4', '#00ACC1',
    '#0097A7', '#00838F', "#0E979B", '#1976D2', '#1565C0',
    '#BA68C8', '#AB47BC', '#9C27B0', '#8E24AA', '#7B1FA2',
    '#6A1B9A', "#5A20A1", '#7E57C2', '#673AB7', '#5E35B1',
    '#F06292', '#EC407A', '#E91E63', '#D81B60', '#C2185B',
    '#AD1457', '#880E4F', '#FF6F94', '#F45C82', '#E84A6F',
    '#FFD54F', '#FFCA28', '#FFC107', '#FFB300', '#FFA000',
    '#FF8F00', '#FF6F00', '#FF8A65', '#FF7043', '#F4511E'
]
COLOR_MAX_CHANGE = 20 # Maximum amount to change the sonde track colors by

def get_track_color() -> str:
    """Get a color for a sonde track"""

    # Pick random color, remove # and convert to RGB
    hex_color = random.choice(SONDE_TRACK_COLORS)[-6:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Apply small random change to each value
    new_r = max(0, min(255, r + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    new_g = max(0, min(255, g + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    new_b = max(0, min(255, b + random.randint(-COLOR_MAX_CHANGE, COLOR_MAX_CHANGE)))
    
    # Convert back to hex
    return f"#{new_r:02x}{new_g:02x}{new_b:02x}"