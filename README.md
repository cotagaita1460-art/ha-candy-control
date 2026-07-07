# Candy Control para Home Assistant

Extensión HACS para controlar lavarropas Candy/Simply-Fi desde Home Assistant.

## Requisitos

- HA con HACS instalado
- Lavarropas Candy Simply-Fi en la misma red

## Instalación

1. En HACS, andá a "Custom Repositories"
2. Agregá la URL: `https://github.com/cotagaita1460-art/ha-candy-control`
3. Categoría: "Integration"
4. Instalá "Candy Control"
5. Reiniciá HA
6. Settings → Integrations → Add → "Candy Control"
7. Ingresá la IP del lavarropas (ej: `192.168.x.x`) y la clave de encriptación XOR

## Servicios disponibles

### `candy_control.start_program`
Inicia un ciclo de lavado.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `pr_nm` | int | `1` | Posición del dial |
| `pr_code` | string | - | Código interno del programa |
| `temp` | int | `40` | Temperatura en °C (0=frio, 20,30,40,60,90) |
| `spin` | int | `10` | RPM/100 (8=800, 10=1000, 12=1200) |
| `steam` | int | `0` | Vapor (0=No, 1=Sí) |
| `dry` | int | `0` | Secado extra |
| `delay` | int | - | Delay en unidades de 30min |

### `candy_control.stop_program`
Detiene el programa actual.

## Botones

- `button.detener_lavarropas` - Detiene el programa
- `button.iniciar_lavarropas_diario_39` - Inicia programa rápido (DIARIO 39', 40°C, 1000 RPM)

## Ejemplo Lovelace

```yaml
type: button
name: Iniciar DIARIO 39'
icon: mdi:play
tap_action:
  action: call-service
  service: candy_control.start_program
  service_data:
    pr_nm: 1
    pr_code: 136
    temp: 40
    spin: 10

type: button
name: Detener
icon: mdi:stop
tap_action:
  action: call-service
  service: candy_control.stop_program
```

## Licencia

MIT
