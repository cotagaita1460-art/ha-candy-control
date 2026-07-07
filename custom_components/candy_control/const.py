"""Constants for the Candy Control integration."""

DOMAIN = "candy_control"
PLATFORMS = ["button", "select"]

CONF_IP_ADDRESS = "ip_address"
CONF_PASSWORD = "password"
CONF_USE_ENCRYPTION = "use_encryption"

MANUFACTURER = "Candy"
DEVICE_NAME = "Lavarropas Candy"

DEFAULT_PROGRAMS = {
    "DIARIO 39'":      {"pr": 1, "pr_code": "136", "temp": 40, "spin": 10, "desc": "Rápido 39 min, carga 4.5kg, temp máx 40°C"},
    "COLOR Y MIXTOS 59'": {"pr": 2, "pr_code": "135", "temp": 40, "spin": 10, "desc": "Color 59 min, carga 9kg, temp máx 40°C"},
    "ALGODÓN PERFECTO 59'": {"pr": 3, "pr_code": "8", "temp": 40, "spin": 10, "desc": "Algodón 59 min, carga 4.5kg, temp máx 40°C"},
    "HIGIENE PLUS 59'": {"pr": 3, "pr_code": "9", "temp": 60, "spin": 10, "desc": "Higiene 59 min, carga 2kg, temp máx 60°C"},
    "DEPORTE PLUS 29'": {"pr": 5, "pr_code": "72", "temp": 30, "spin": 10, "desc": "Deporte 29 min, carga 4.5kg, temp máx 30°C"},
    "DELICADOS 59'":   {"pr": 6, "pr_code": "4", "temp": 30, "spin": 4, "desc": "Delicados 59 min, carga 2kg, temp máx 30°C"},
    "ECO 14'":         {"pr": 7, "pr_code": "7", "temp": 30, "spin": 10, "desc": "Eco 14 min, carga 4.5kg, temp máx 30°C"},
    "ECO 30'":         {"pr": 7, "pr_code": "6", "temp": 30, "spin": 10, "desc": "Eco 30 min, carga 4.5kg"},
    "ECO 44'":         {"pr": 7, "pr_code": "5", "temp": 30, "spin": 10, "desc": "Eco 44 min, carga 4.5kg"},
    "ACLARADOS":       {"pr": 8, "pr_code": "35", "temp": 0, "spin": 10, "desc": "Solo aclarados, Frío"},
    "DESAGÜE & CENTRIFUGADO": {"pr": 9, "pr_code": "36", "temp": 0, "spin": 10, "desc": "Desagüe y centrifugado"},
    "LANA/A MANO":     {"pr": 11, "pr_code": "3", "temp": 40, "spin": 10, "desc": "Lana / A mano, carga 2kg, temp máx 40°C"},
    "SINTÉTICOS":      {"pr": 13, "pr_code": "32", "temp": 40, "spin": 10, "desc": "Sintéticos y ropa de color"},
    "ECO 20°":         {"pr": 12, "pr_code": "11", "temp": 20, "spin": 10, "desc": "Eco 20°C, carga 9kg, bajo consumo"},
    "ALGODÓN":         {"pr": 14, "pr_code": "65", "temp": 40, "spin": 10, "desc": "Algodón, carga 9kg, temp máx 90°C"},
    "ALGODÓN RESISTENTE": {"pr": 15, "pr_code": "66", "temp": 60, "spin": 10, "desc": "Algodón resistente, carga 9kg, temp máx 90°C"},
}
