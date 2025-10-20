from enum import Enum


class TypeOfCircuit(Enum):
    """Тип отопительного контура."""

    BOILER = 'boiler'
    CONSUMER = 'consumer'
    COOLING = 'cooling'
    DHW = 'dhw'


class TypeOfSensor(Enum):
    """Тип сенсоров."""

    TEMPERATURE = 'temperature'
    VOLTAGE = 'voltage'
    PRESSURE = 'pressure'
    HUMIDITY = 'humidity'
    OPENING = 'opening'
    MOTION = 'motion'
    LEAKAGE = 'leakage'
    SMOKE = 'smoke'
    ROOM_THERMOSTAT = 'room_thermostat'
    BOILER_FAILURE = 'boiler_failure'
    POWER_SOURCE = 'power_source'
    MODULATION = 'modulation'
    DISCRETE = 'discrete'
    DHW_SPEED = 'dhw_speed'
    GAS = 'gas'
    OTHER = 'other'


class StateOfSensor(Enum):
    """Тип сенсоров."""

    UNKNOWN = 'unknown'
    OK = 'ok'
    FAILURE = 'failure'
    ALARM = 'alarm'
    SILENT_ALARM = 'silent_alarm'


class SignalOfSensor(Enum):
    """Тип сенсоров."""

    NO_SIGNAL = 'no_signal'
    WEAK = 'weak'
    FAIR = 'fair'
    GOOD = 'good'
    EXCELLENT = 'excellent'


class GuardState(Enum):
    """Состояние охраны."""

    UNKNOWN = 'unknown'
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    DISABLING = 'disabling'
    ENABLING = 'enabling'
