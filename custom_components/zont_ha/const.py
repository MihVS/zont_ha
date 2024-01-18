from homeassistant.const import (
    TEMP_CELSIUS, UnitOfElectricPotential, PERCENTAGE, UnitOfPressure
)

DOMAIN = 'zont_ha'
MANUFACTURER = 'MicroLine'

ZONT_API_URL = "https://lk.zont-online.ru/api/widget/v2/"

URL_SEND_COMMAND_ZONT_OLD = "https://lk.zont-online.ru/api/send_z3k_command"

URL_GET_DEVICES = 'https://lk.zont-online.ru/api/widget/v2/get_devices'
URL_SET_TARGET_TEMP = 'https://lk.zont-online.ru/api/widget/v2/set_target_temp'
URL_SET_GUARD = 'https://lk.zont-online.ru/api/widget/v2/set_guard'
URL_ACTIVATE_HEATING_MODE = (
    'https://lk.zont-online.ru/api/widget/v2/activate_heating_mode'
)
URL_TRIGGER_CUSTOM_BUTTON = (
    'https://lk.zont-online.ru/api/widget/v2/trigger_custom_button'
)
URL_GET_TOKEN = 'https://lk.zont-online.ru/api/authtoken/get'

VALID_UNITS = {
    'temperature': TEMP_CELSIUS,
    'humidity': PERCENTAGE,
    'voltage': UnitOfElectricPotential.VOLT,
    'modulation': PERCENTAGE,
    'pressure': UnitOfPressure.BAR,
    'leakage': UnitOfElectricPotential.VOLT,
    'motion': UnitOfElectricPotential.VOLT,
    'smoke': UnitOfElectricPotential.VOLT,
    'opening': UnitOfElectricPotential.VOLT,
    'room_thermostat': UnitOfElectricPotential.VOLT,
    'boiler_failure': UnitOfElectricPotential.VOLT,
    'power_source': UnitOfElectricPotential.VOLT,
    'discrete': UnitOfElectricPotential.VOLT,
    'dhw_speed': 'л/мин'
}
BINARY_SENSOR_TYPES = ('leakage', 'smoke', 'opening', 'motion')

MIN_TEMP_AIR = 5
MAX_TEMP_AIR = 35
MIN_TEMP_GVS = 25
MAX_TEMP_GVS = 75
MIN_TEMP_FLOOR = 15
MAX_TEMP_FLOOR = 45
MATCHES_GVS = ('гвс', 'горяч', 'вода',)
MATCHES_FLOOR = ('пол', 'тёплый',)

BUTTON_ZONT = 'button'
SWITCH_ZONT = 'toggle_button'

PLATFORMS = [
    'sensor',
    'climate',
    'button',
    'switch',
    'alarm_control_panel',
    'binary_sensor'
]

COUNTER_REPEAT = 18
TIME_OUT_REPEAT = 10
TIME_OUT_REQUEST = 2
