"""Constants for the Candy Control integration."""

DOMAIN = "candy_control"
PLATFORMS = ["button", "select"]

CONF_IP_ADDRESS = "ip_address"
CONF_PASSWORD = "password"
CONF_USE_ENCRYPTION = "use_encryption"

MANUFACTURER = "Candy"
DEVICE_NAME = "Lavarropas Candy"

DEFAULT_PROGRAMS = {
    "DIARIO 39'":      {"pr": 1, "pr_code": "136", "temp": 40, "spin": 10, "desc": "Lavado excelente para media carga en 39 min. Recomendado para colada diaria medianamente sucia."},
    "COLOR Y MIXTOS 59'": {"pr": 2, "pr_code": "135", "temp": 40, "spin": 10, "desc": "Lava juntos todo tipo de tejidos y colores que no decoloran. Carga completa, resultados en 59 min."},
    "ALGODÓN PERFECTO 59'": {"pr": 3, "pr_code": "8", "temp": 40, "spin": 10, "desc": "Resultados fantásticos con algodón. Reduce el tiempo de lavado a temperaturas medias. Llene hasta la mitad."},
    "HIGIENE PLUS 59'": {"pr": 3, "pr_code": "9", "temp": 60, "spin": 10, "desc": "Máxima desinfección contra bacterias en 59 min. Lava a 60°C. Recomendado para cargas pequeñas."},
    "DEPORTE PLUS 29'": {"pr": 5, "pr_code": "72", "temp": 30, "spin": 10, "desc": "Elimina suciedad de prendas técnicas y deportivas. Lava a baja temperatura en 29 min. Pequeñas cargas."},
    "DELICADOS 59'":   {"pr": 6, "pr_code": "4", "temp": 30, "spin": 4, "desc": "Para prendas delicadas y tejidos preciados. Lava a baja temperatura en 59 min. Cargas pequeñas."},
    "ECO 14'":         {"pr": 7, "pr_code": "7", "temp": 30, "spin": 10, "desc": "Ahorro total de agua, energía, detergente y tiempo. 14 min a temperatura media. Cualquier tejido."},
    "ECO 30'":         {"pr": 7, "pr_code": "6", "temp": 30, "spin": 10, "desc": "Ahorro total de agua, energía, detergente y tiempo. 30 min a temperatura media. Cualquier tejido."},
    "ECO 44'":         {"pr": 7, "pr_code": "5", "temp": 30, "spin": 10, "desc": "Ahorro total de agua, energía, detergente y tiempo. 44 min a temperatura media. Cualquier tejido."},
    "ACLARADOS":       {"pr": 8, "pr_code": "35", "temp": 0, "spin": 10, "desc": "3 aclarados con centrifugado intermedio. Para aclarar todo tipo de tejidos tras lavado a mano."},
    "DESAGÜE & CENTRIFUGADO": {"pr": 9, "pr_code": "36", "temp": 0, "spin": 10, "desc": "Escurrido y centrifugado a máxima velocidad. Cancelable o reducible."},
    "LANA/A MANO":     {"pr": 11, "pr_code": "3", "temp": 40, "spin": 10, "desc": "Ciclo especial para tejidos de lana y prendas que deban lavarse a mano. Carga 2kg."},
    "SINTÉTICOS":      {"pr": 13, "pr_code": "32", "temp": 40, "spin": 10, "desc": "Lava tejidos y colores diferentes juntos. Rotación optimizada. Reduce arrugas."},
    "ECO 20°":         {"pr": 12, "pr_code": "11", "temp": 20, "spin": 10, "desc": "Lava diferentes tejidos y colores a solo 20°C. Consume ~40% de un programa convencional."},
    "ALGODÓN":         {"pr": 14, "pr_code": "65", "temp": 40, "spin": 10, "desc": "Para ropa de algodón con suciedad normal. El más eficiente en consumo combinado de agua y energía."},
    "ALGODÓN RESISTENTE": {"pr": 15, "pr_code": "66", "temp": 60, "spin": 10, "desc": "Resultado de lavado perfecto. Centrifugado final a máxima velocidad. Elimina manchas con eficacia."},
}
