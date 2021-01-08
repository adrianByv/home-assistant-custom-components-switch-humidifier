# Switch Humidifier

Switch Humidifier Platform for Home-Assistant (<http://www.home-assistant.io>)

A platform for humidity entity based on a switch and a humidity sensor.

`Only` support `Humidifier` or `Dehumidifier`. Humidifier-dehumidifier is not supported.

I develop it to use with a humidity device that I manage with a sonoff th 16 (with temperature and humidity sensors). With this platform you can set the humidity target and it will turn on or off the switch based on the sensor humidity value, the target humidity and the entity state. As a thermostat that can be turned on, but not hotting or cooling based on the temperature.

If the switch is manually changed:

- If the `entity` is `off` and the switch is `turnerd on`, it `active` the entity.
- If the `entity` is `on` and the switch is `turnerd off`, it `deactive` the entity. 
- If the `entity` is `on`, but the switch off (based on the humidity and target) and the switch is `turned on` it mantain the entity `active` and inmediatly turn the switch off again.

## Installation

- Copy all files in custom_components/switch_humidifier to your config/custom_components/switch_humidifier/ directory.
- Restart Home-Assistant.
- Add the configuration to your configuration.yaml file.

### Usage

To use this component in your installation, add the following to your configuration.yaml file:

### Example configuration.yaml entry

``` yalm
humidifier: 
  - platform: switch_humidifier
    name: Switch Deshumidifier
    switch_id: switch.deshumidifier
    sensor_id: sensor.humidity
    type: dehumidifier
    start_delta: 0.2
    stop_delta: 0.2
```

### Parameters

- `name` (Optional): The platform name
- `switch_id` (Required): The switch entintity id
- `sensor_id` (Required): The humidity sensor entintity
- `type` (Optional): Posible values are `humidifier` or `dehumidifier`
  - Default: `dehumidifier`
- `start_delta` (Optional): The delta % added to start if it's off
  - Default: `0.1`
- `stop_delta` (Optional): The delta % added to stop if it's on
  - Default: `0.1`

It should also support homekit.

## Homekit

To use with homekit you need to especify the humidity sensor as `linked_humidity_sensor` in the `entity_config`

```yalm
homekit:
- filter:
    include_entities:
      - humidifier.switch_humidifier
      - sensor.humidity
  entity_config:
    humidifier.switch_humidifier:
      linked_humidity_sensor: sensor.humidity
```
