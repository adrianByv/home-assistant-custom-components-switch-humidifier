"""Switch Humidifier Platform"""
import logging
import json
import os

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.helpers.event import track_state_change, async_track_state_change_event

from homeassistant.components.humidifier import (
  ATTR_HUMIDITY,
  ATTR_MAX_HUMIDITY,
  ATTR_MIN_HUMIDITY,
  DEVICE_CLASS_DEHUMIDIFIER,
  DEVICE_CLASS_HUMIDIFIER,
  SUPPORT_MODES,
  PLATFORM_SCHEMA,
  HumidifierEntity,
)
from homeassistant.const import (
  CONF_NAME,
  SERVICE_TURN_ON,
  SERVICE_TURN_OFF,
  SERVICE_TOGGLE,
  STATE_ON,
  STATE_OFF
)

import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

CONF_NAME = 'name'
DEFAULT_NAME = 'humidifier'

CONF_SENSOR_ID = 'sensor_id'
CONF_SWITCH_ID = 'switch_id'
CONF_TYPE = 'type'
CONF_START_DELTA = 'start_delta'
CONF_STOP_DELTA = 'stop_delta'


DEHUMIDIFIER_TYPE = 'dehumidifier'
HUMIDIFIER_TYPE = 'humidifier'

TYPES = [
  DEHUMIDIFIER_TYPE,
  HUMIDIFIER_TYPE
]

DEFAULT_TYPE = DEHUMIDIFIER_TYPE
DEFAULT_HUMIDITY = 50
DEFAULT_START_DELTA = 0.1
DEFAULT_STOP_DELTA = 0.1
DEFAULT_SWITCH_STATE = STATE_OFF
MIN_HUMIDITY = 0
MAX_HUMIDITY = 100

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
  {
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_SENSOR_ID): cv.string,
    vol.Required(CONF_SWITCH_ID): cv.string,
    vol.Optional(CONF_TYPE, default=DEFAULT_TYPE): vol.All(cv.string, vol.In(TYPES)),
    vol.Optional(CONF_START_DELTA, default=DEFAULT_START_DELTA): vol.Coerce(float),
    vol.Optional(CONF_STOP_DELTA, default=DEFAULT_STOP_DELTA): vol.Coerce(float),
  }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
  """Set up the dehumidifier platform."""
  name = config[CONF_NAME]
  sensor_id = config[CONF_SENSOR_ID]
  switch_id = config[CONF_SWITCH_ID]
  device_class = DEVICE_CLASS_DEHUMIDIFIER
  if config[CONF_TYPE] == HUMIDIFIER_TYPE:
    device_class = DEVICE_CLASS_HUMIDIFIER
  start_delta = config[CONF_START_DELTA]
  stop_delta = config[CONF_STOP_DELTA]
  devices = []
  switchHumidifier = SwitchHumidifier(name, sensor_id, switch_id, device_class, start_delta, stop_delta)
  devices.append(switchHumidifier)
  add_entities(devices, True)

  # Track sensor or switch state changes.
  track_state_change(hass, [sensor_id, switch_id], switchHumidifier._state_changed)

  return True

class SwitchHumidifier(HumidifierEntity):
	
  def __init__(self, name, sensor_id, switch_id, device_class, start_delta, stop_delta):
    """Initialize the humidifier."""
    self._sensor_id = sensor_id
    self._switch_id = switch_id  

    self._humidity = DEFAULT_HUMIDITY

    self._switch_state = DEFAULT_SWITCH_STATE

    self._is_on = DEFAULT_SWITCH_STATE == STATE_ON

    self._device_class = device_class

    self._start_delta = start_delta

    self._stop_delta = stop_delta

    # To cheack if the switch state change if fired by the platform
    self._self_changed_switch = False
    
    self._name = name

    # Persistence file to store persistent data
    self._persistence_final_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persistence.json")

    try:
      if os.path.isfile(self._persistence_final_path):
        self._persistence_json = json.load(open(self._persistence_final_path, 'r'))
      else:
        _LOGGER.warning("file doesnt exist")
        self._persistence_json = json.loads('{"target": ' + str(DEFAULT_HUMIDITY) + '}')

      self._target_humidity = self._persistence_json['target']
      self.save_target()

    except Exception as e:
      _LOGGER.error("Error occured loading: %s", str(e))
      self._target_humidity = DEFAULT_HUMIDITY

  def save_target(self): 
    """set target humidity to persistent JSON and store it."""
    self._persistence_json['target'] = self._target_humidity
    self.persistence_save()

  def persistence_save(self): 
    """Store persistent JSON as file."""
    if self._persistence_json is not None: #Check we have something to save
      try:
        with open(self._persistence_final_path, 'w') as fil:
          fil.write(json.dumps(self._persistence_json, ensure_ascii=False))
      except Exception as e:
        _LOGGER.error("Error occured saving: %s", str(e))

  def update(self):
    """Update called periodically"""
    self._update_switch() 

  @property
  def name(self):
    """Return the name of the humidifier."""
    return self._name

  @property
  def target_humidity(self):
    """Return the target humidity."""
    return self._target_humidity

  @property
  def min_humidity(self):
    """Return the target humidity."""
    return MIN_HUMIDITY

  @property
  def max_humidity(self):
    """Return the target humidity."""
    return MAX_HUMIDITY
      
  # def supported_features(self):
  #   """Return the list of supported features."""
  #   return (SUPPORT_MODES)

  @property
  def is_on(self):
    """Return if the dehumidifier is on."""
    return self._is_on

  @property
  def device_class(self):
    """Return Device class."""
    _LOGGER.debug('device_class')
    return self._device_class

  def set_humidity(self, humidity):
    """Set target humidity."""
    _LOGGER.debug('set_humidity')
    self._target_humidity = humidity
    self.save_target()

  def turn_on(self, **kwargs):
    """Turn the device ON."""
    _LOGGER.debug('turn_on')
    self._is_on = True
    self._update_switch()

  def turn_off(self, **kwargs):
    """Turn the device OFF."""
    _LOGGER.debug('turn_off')
    self._is_on = False
    self._update_switch()

  ############################################################

  def _state_changed(self, entity_id, old_state, new_state):
    """Called on sensor or switch state change"""
    if not new_state is None and not new_state.state == 'unknown' and not new_state.state == 'unavailable' and old_state.state != new_state.state:
      # old switch power and new switch power must be different
      if entity_id == self._sensor_id:
        # Update humidity value
        self._humidity = float(new_state.state)
        self._update_switch()
      elif entity_id == self._switch_id:
        # Update switch state
        self._switch_state = new_state.state
        if self._self_changed_switch == True:
          # Platform fired the switch state change
          self._self_changed_switch = False
        else:
          # Switch state changed by external source
          new_is_on = self._switch_state == STATE_ON
          if not new_is_on == self._is_on:
            self._is_on = new_is_on
            # Update state of entity
            self.async_write_ha_state()
            self._update_switch() 

  def _update_switch(self):
    """Manage switch based on the state."""
    if self._is_on == True:
      # Platform is on, check humidity
      if self.device_class == DEVICE_CLASS_DEHUMIDIFIER:
        if self._switch_state == STATE_ON and self._humidity < self._target_humidity - self._stop_delta:
          self._turn_switch_off()
        elif self._switch_state == STATE_OFF and self._humidity > (self._target_humidity + self._start_delta):
          self._turn_switch_on()
      elif self.device_class == DEVICE_CLASS_HUMIDIFIER:
        if self._switch_state == STATE_ON and self._humidity > (self._target_humidity + self._stop_delta):
          self._turn_switch_off()
        elif self._switch_state == STATE_OFF and self._humidity < (self._target_humidity - self._start_delta):
          self._turn_switch_on()
    else:
      # Platform is off
      self._turn_switch_off()

  def _turn_switch_on(self):
    """Turn the switch ON if needed."""
    if self._switch_state == STATE_OFF:
      self._self_changed_switch = True
      self.hass.services.call("homeassistant", SERVICE_TURN_ON, {"entity_id": self._switch_id}, False)


  def _turn_switch_off(self):
    """Turn the switch OFF if needed."""
    if self._switch_state == STATE_ON:
      self._self_changed_switch = True
      self.hass.services.call("homeassistant", SERVICE_TURN_OFF, {"entity_id": self._switch_id}, False)