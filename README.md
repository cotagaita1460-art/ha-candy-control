# Candy Control para Home Assistant v1.1.1

Extensión HACS para controlar lavarropas Candy/Simply-Fi desde Home Assistant.

## Requisitos

- HA con HACS instalado
- Lavarropas Candy Simply-Fi en la misma red
- Home Assistant 2025.1.0 o superior

## Instalación

1. En HACS, andá a "Custom Repositories"
2. Agregá la URL: `https://github.com/cotagaita1460-art/ha-candy-control`
3. Categoría: "Integration"
4. Instalá "Candy Control"
5. Reiniciá HA
6. Settings → Integrations → Add → "Candy Control"
7. Ingresá la IP del lavarropas (ej: `192.168.x.x`) y la clave de encriptación XOR

## Entidades

- `select.lavarropas_candy_programa_lavarropas` - Selector de programas (16 programas con descripciones del manual)
- `button.lavarropas_candy_iniciar_lavarropas` - Inicia el programa seleccionado
- `button.lavarropas_candy_detener_lavarropas` - Detiene el programa actual

## Servicios

### `candy_control.start_program`
Inicia un ciclo de lavado con parámetros manuales.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `pr_nm` | int | requerido | Posición del dial (1-15) |
| `pr_code` | string | requerido | Código interno del programa |
| `temp` | int | `40` | Temperatura en °C (0,20,30,40,60,90) |
| `spin` | int | `10` | RPM/100 (0-16) |
| `steam` | int | `0` | Vapor (0/1) |
| `dry` | int | `0` | Secado extra (0/1) |
| `delay` | int | - | Inicio diferido en unidades de 30min |

### `candy_control.stop_program`
Detiene el programa actual.

### `candy_control.set_programs`
Agrega o reemplaza programas personalizados.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `programs` | list | Lista de programas con name, pr, pr_code, temp, spin, desc |

## Dashboard recomendado

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: select.lavarropas_candy_programa_lavarropas
    name: Programa
    icon: mdi:washing-machine
  - type: markdown
    title: Descripción
    content: |
      {{ state_attr('select.lavarropas_candy_programa_lavarropas', 'description') }}
  - type: horizontal-stack
    cards:
      - type: button
        name: INICIAR
        icon: mdi:play
        tap_action:
          action: call-service
          service: button.press
          service_data:
            entity_id: button.lavarropas_candy_iniciar_lavarropas
      - type: button
        name: DETENER
        icon: mdi:stop
        tap_action:
          action: call-service
          service: button.press
          service_data:
            entity_id: button.lavarropas_candy_detener_lavarropas
```

## Programas incluidos

| Programa | Temp | Centrifugado |
|----------|------|-------------|
| DIARIO 39' | 40°C | 1000 RPM |
| COLOR Y MIXTOS 59' | 40°C | 1000 RPM |
| ALGODÓN PERFECTO 59' | 40°C | 1000 RPM |
| HIGIENE PLUS 59' | 60°C | 1000 RPM |
| DEPORTE PLUS 29' | 30°C | 1000 RPM |
| DELICADOS 59' | 30°C | 400 RPM |
| ECO 14'/30'/44' | 30°C | 1000 RPM |
| ACLARADOS | Frío | 1000 RPM |
| DESAGÜE & CENTRIFUGADO | Frío | 1000 RPM |
| LANA/A MANO | 40°C | 1000 RPM |
| SINTÉTICOS | 40°C | 1000 RPM |
| ECO 20° | 20°C | 1000 RPM |
| ALGODÓN | 40°C | 1000 RPM |
| ALGODÓN RESISTENTE | 60°C | 1000 RPM |

## Licencia

MIT
