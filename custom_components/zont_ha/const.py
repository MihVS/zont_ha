from homeassistant.const import (
    UnitOfTemperature, UnitOfElectricPotential, PERCENTAGE, UnitOfPressure,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT
)

DOMAIN = 'zont_ha'
MANUFACTURER = 'MicroLine'
CONFIGURATION_URL = 'https://lk.zont-online.ru/'

ZONT_API_URL_ROOT = 'https://lk.zont-online.ru/api/'
ZONT_API_URL = ZONT_API_URL_ROOT + 'widget/v2/'

URL_GET_DEVICES_OLD = ZONT_API_URL_ROOT + 'devices'
URL_SEND_COMMAND_ZONT_OLD = ZONT_API_URL_ROOT + 'send_z3k_command'

URL_SEND_COMMAND_ZONT = ZONT_API_URL + 'activate_heating_mode'
URL_GET_DEVICES = ZONT_API_URL + 'get_devices'
URL_SET_TARGET_TEMP = ZONT_API_URL + 'set_target_temp'
URL_SET_GUARD = ZONT_API_URL + 'set_guard'
URL_ACTIVATE_HEATING_MODE = ZONT_API_URL + 'activate_heating_mode'
URL_TRIGGER_CUSTOM_BUTTON = ZONT_API_URL + 'trigger_custom_button'

URL_GET_TOKEN = ZONT_API_URL_ROOT + 'authtoken/get'

VALID_UNITS = {
    'temperature': UnitOfTemperature.CELSIUS,
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
    'dhw_speed': 'л/мин',
    'txt': None,
    'rssi': SIGNAL_STRENGTH_DECIBELS_MILLIWATT
}
BINARY_SENSOR_TYPES = ('leakage', 'smoke', 'opening', 'motion')

MIN_TEMP_AIR = 5
MAX_TEMP_AIR = 35
MIN_TEMP_GVS = 25
MAX_TEMP_GVS = 75
MIN_TEMP_FLOOR = 15
MAX_TEMP_FLOOR = 45
MATCHES_GVS = ('гвс', 'горяч', 'вода', 'бкн', 'гидро', 'подача')
MATCHES_FLOOR = ('пол', 'тёплый',)

BUTTON_ZONT = 'button'
SWITCH_ZONT = 'toggle_button'

PLATFORMS = [
    'sensor',
    'climate',
    'button',
    'switch',
    'alarm_control_panel',
    'binary_sensor',
    'device_tracker'
]

COUNTER_REPEAT = 18
COUNTER_CONNECT = 10
TIME_OUT_UPDATE_DATA = 10
TIME_OUT_REPEAT = 10
TIME_OUT_REQUEST = 2
TIME_UPDATE = 60

MODELS_THERMOSTAT_ZONT = ('T100', 'T102')

STATES_CAR = {
    'engine_on': 'Двигатель заведён',
    'engine_block': 'Состояние блокировки двигателя',
    'siren': 'Состояние сирены',
    'door_front_left': 'Передняя левая дверь открыта',
    'door_front_right': 'Передняя правая дверь открыта',
    'door_rear_left': 'Задняя левая дверь открыта',
    'door_rear_right': 'Задняя правая дверь открыта',
    'trunk': 'Багажник открыт',
    'hood': 'Капот открыт'
}

NO_ERROR = 'Ошибок нет'

HEATING_MODES = {
    'комфорт': 'mdi:emoticon-happy-outline',
    'эконом': 'mdi:leaf-circle-outline',
    'лето': 'mdi:weather-sunny',
    'расписание': 'mdi:clock-outline',
    'выкл': 'mdi:power',
    'тишина': 'mdi:sleep',
    'дома': 'mdi:home-outline',
    'не дома': 'mdi:home-off-outline',
    'гвс': 'mdi:water-boiler',
}
