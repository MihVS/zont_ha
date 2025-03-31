from homeassistant.const import (
    UnitOfTemperature, UnitOfElectricPotential, PERCENTAGE, UnitOfPressure,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfVolumeFlowRate, UnitOfSpeed,
    UnitOfVolume, UnitOfFrequency, UnitOfPower, UnitOfApparentPower,
    UnitOfReactivePower, CONCENTRATION_PARTS_PER_MILLION, UnitOfEnergy
)

DOMAIN = 'zont_ha'
MANUFACTURER = 'MicroLine''ab-log'
ENTRIES = 'entries'
CURRENT_ENTITY_IDS = 'current_entity_ids'
CONFIGURATION_URL = 'https://my.zont.online/'

ZONT_API_URL_ROOT = 'https://my.zont.online/api/'
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

UNIT_BY_TYPE = {
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
    'power_source': UnitOfEnergy.KILO_WATT_HOUR,
    'discrete': UnitOfElectricPotential.VOLT,
    'signal_strength': SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    'battery': PERCENTAGE
}

VALID_UNITS = {
    'л/мин': UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    'л': UnitOfVolume.LITERS,
    'м³/ч': UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    'txt': None,
    'дБм': SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    'бар': UnitOfPressure.BAR,
    '°': UnitOfTemperature.CELSIUS,
    '%': PERCENTAGE,
    'В': UnitOfElectricPotential.VOLT,
    'км/ч': UnitOfSpeed.KILOMETERS_PER_HOUR,
    'Гц': UnitOfFrequency.HERTZ,
    'Вт': UnitOfPower.WATT,
    'ВА': UnitOfApparentPower.VOLT_AMPERE,
    'ВАР': UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
    'кВт•ч': UnitOfEnergy.KILO_WATT_HOUR,
    'ppm': CONCENTRATION_PARTS_PER_MILLION,
    'battery': PERCENTAGE
}

ZONT_SENSOR_TYPE = {
    'dhw_speed': 'volume_flow_rate'
}

SENSOR_TYPE_ICON = {
    'boiler_failure': 'mdi:wrench-outline',
    'dhw_speed': 'mdi:waves-arrow-right',
    'modulation': 'mdi:fire'
}

VALID_TYPE_SENSOR = {
    'pressure': 'бар',
    'temperature': '°',
    'speed': 'км/ч',
    'volume': 'л',
    'volume_flow_rate': ('л/ч', 'м³/ч'),
    'frequency': ('Гц', 'об/мин'),
    'power': ('Вт', 'ВА'),
    'reactive_power': 'ВАР',
    'volatile_organic_compounds_parts': 'ppm',
    'energy': 'кВт•ч'
}

BINARY_SENSOR_TYPES = ('leakage', 'smoke', 'opening', 'motion', 'discrete')

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
    'эко': 'mdi:leaf-circle-outline',
    'лето': 'mdi:weather-sunny',
    'расписание': 'mdi:clock-outline',
    'выкл': 'mdi:power',
    'тишина': 'mdi:sleep',
    'дома': 'mdi:home-outline',
    'не дома': 'mdi:home-off-outline',
    'гвс': 'mdi:water-boiler',
}

PERCENT_BATTERY = {
    3.0: 95,
    2.9: 80,
    2.8: 65,
    2.7: 50,
    2.6: 35,
    2.5: 20,
    2.4: 10,
    2.3: 5
}
