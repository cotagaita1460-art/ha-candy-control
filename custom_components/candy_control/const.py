"""Constants for the Candy Control integration."""

DOMAIN = "candy_control"
PLATFORMS = ["button", "select"]

CONF_IP_ADDRESS = "ip_address"
CONF_PASSWORD = "password"
CONF_USE_ENCRYPTION = "use_encryption"

MANUFACTURER = "Candy"
DEVICE_NAME = "Lavarropas Candy"

PROGRAMS = {
    "DIARIO 39'": {"pr": 1, "pr_code": "136", "temp": 40, "spin": 10},
    "COLOR Y MIXTOS 59'": {"pr": 2, "pr_code": "135", "temp": 40, "spin": 10},
    "ALGODÓN PERFECTO 59'": {"pr": 3, "pr_code": "8", "temp": 40, "spin": 10},
    "DEPORTE PLUS 29'": {"pr": 5, "pr_code": "72", "temp": 30, "spin": 10},
    "DELICADOS 59'": {"pr": 6, "pr_code": "4", "temp": 30, "spin": 4},
    "ECO 14'": {"pr": 7, "pr_code": "7", "temp": 30, "spin": 10},
    "ACLARADOS": {"pr": 8, "pr_code": "35", "temp": 0, "spin": 10},
    "DESAGÜE & CENTRIFUGADO": {"pr": 9, "pr_code": "36", "temp": 0, "spin": 10},
    "LANA/A MANO": {"pr": 11, "pr_code": "3", "temp": 40, "spin": 10},
    "ECO 20°": {"pr": 12, "pr_code": "11", "temp": 20, "spin": 10},
    "SINTÉTICOS": {"pr": 13, "pr_code": "32", "temp": 40, "spin": 10},
    "ALGODÓN": {"pr": 14, "pr_code": "65", "temp": 40, "spin": 10},
    "ALGODÓN RESISTENTE": {"pr": 15, "pr_code": "66", "temp": 60, "spin": 10},
}
