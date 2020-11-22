"""Switch Humidifier Platform"""
import logging

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


DEHUMIDIFIER_TYPE = 'dehumidifier'
HUMIDIFIER_TYPE = 'humidifier'

TYPES = [
  DEHUMIDIFIER_TYPE,
  HUMIDIFIER_TYPE
]

DEFAULT_TYPE = DEHUMIDIFIER_TYPE
DEFAULT_HUMIDITY = 50
DEFAULT_SWITCH_STATE = STATE_OFF
MIN_HUMIDITY = 0
MAX_HUMIDITY = 100

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
  {
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_SENSOR_ID): cv.string,
    vol.Required(CONF_SWITCH_ID): cv.string,
    vol.Optional(CONF_TYPE, default=DEFAULT_TYPE): vol.All(cv.string, vol.In(TYPES)),
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
  devices = []
  switchHumidifier = SwitchHumidifier(name, sensor_id, switch_id, device_class)
  devices.append(switchHumidifier)
  add_entities(devices, True)

  # Track sensor or switch state changes.
  track_state_change(hass, [sensor_id, switch_id], switchHumidifier._state_changed)

  return True

class SwitchHumidifier(HumidifierEntity):
	
  def __init__(self, name, sensor_id, switch_id, device_class):
    """Initialize the humidifier."""
    self._sensor_id = sensor_id
    self._switch_id = switch_id  

    self._target_humidity = DEFAULT_HUMIDITY

    self._humidity = DEFAULT_HUMIDITY

    self._switch_state = DEFAULT_SWITCH_STATE

    self._is_on = DEFAULT_SWITCH_STATE == STATE_ON

    self._device_class = device_class

    # To cheack if the switch state change if fired by the platform
    self._self_changed_switch = False
    
    self._name = name

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
    if not new_state is None and not new_state.state == 'unknown' and not new_state.state == 'unavailable':
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
        self._turn_switch_on() if self._target_humidity < self._humidity else self._turn_switch_off()
      elif self.device_class == DEVICE_CLASS_HUMIDIFIER:
        self._turn_switch_on() if self._target_humidity > self._humidity else self._turn_switch_off()
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