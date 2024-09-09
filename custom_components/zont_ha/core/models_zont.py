from datetime import datetime

from pydantic import BaseModel, validator, root_validator

from ..const import NO_ERROR


class BaseEntityZONT(BaseModel):
    """Базовая модель сущностей контроллера"""

    id: int | str
    name: str


class ControlEntityZONT(BaseEntityZONT):
    """Базовая модель для управляемых сущностей"""
    pass


class HeatingCircuitZONT(ControlEntityZONT):
    """Контур отопления"""

    status: str | None
    active: bool
    actual_temp: float | None
    is_off: bool
    target_temp: float | None
    current_mode: int | None
    target_min: int | str | None
    target_max: int | str | None


class HeatingModeZONT(ControlEntityZONT):
    """Отопительные режимы"""

    can_be_applied: bool
    color: str | None


class BoilerCircuitZONT(BaseEntityZONT):
    """Котловые контура"""

    active: bool
    status: str | None
    target_temp: float | None
    water_min_temp: float | None
    water_max_temp: float | None
    water_temp: float | None
    air_temp: float | None
    dhw_temp: float | None
    rwt_temp: float | None
    modulation_level: float | None
    pressure: float | None
    dhw_speed: float | None
    outside: float | None
    error_oem: str | None = NO_ERROR
    error_text: str | None = ''


class BoilerModeZONT(ControlEntityZONT):
    """Котловые режимы"""

    can_be_applied: bool
    color: str | None


class SensorZONT(BaseEntityZONT):
    """Сенсоры"""

    type: str
    status: str
    value: float | str | None
    triggered: bool | None
    unit: str | None
    battery: float | None
    rssi: float | None

    @root_validator
    def create_unique_id(cls, values):
        values['id'] = (f'{values.get('id', 'unknown_id')}_'
                        f'{values.get('type', 'unknown_type')}')
        return values


class OTSensorZONT(SensorZONT):
    """Сенсоры котлов"""

    boiler_adapter_id: int


class GuardZoneZONT(ControlEntityZONT):
    """Охранная зона"""

    state: str
    alarm: bool


class CustomControlZONT(ControlEntityZONT):
    """Пользовательский элемент управления"""

    name: dict | str
    type: str
    status: bool | None = None


class ScenarioZONT(ControlEntityZONT):
    """Сценарий"""

    pass


class AutoStart(BaseModel):
    """Модель автостарта автомобиля"""

    available: bool
    status: str
    until: datetime = None


class CarView(BaseModel):
    """Модель внешнего вида автомобиля"""

    model: str


class Position(BaseModel):
    """Модель местонахождения автомобиля"""

    x: float
    y: float
    time: datetime


class CarStateZONT(BaseModel):
    """Модель статуса автомобиля"""

    engine_on: bool
    autostart: AutoStart
    engine_block: bool
    siren: bool
    door_front_left: bool
    door_front_right: bool
    door_rear_left: bool
    door_rear_right: bool
    trunk: bool
    hood: bool
    power_source: str
    car_view: CarView
    position: Position
    address: str


class VersionZONT(BaseModel):
    """Модель версии прошивки и железа устройств"""

    hardware: str
    software: str


class DeviceInfoZONT(BaseModel):
    """Модель информации девайса"""

    id: str
    model: str
    widget_type: str | None
    version: VersionZONT | None


class DeviceZONT(BaseEntityZONT):
    """Модель контроллера"""

    model: str
    online: bool
    widget_type: str | None
    heating_circuits: list[HeatingCircuitZONT] = []
    heating_modes: list[HeatingModeZONT] = []
    boiler_circuits: list[BoilerCircuitZONT] = []
    boiler_modes: list[BoilerModeZONT] = []
    sensors: list[SensorZONT] = []
    ot_sensors: list[OTSensorZONT] = []
    guard_zones: list[GuardZoneZONT] | GuardZoneZONT = []
    custom_controls: list[CustomControlZONT] = []
    scenarios: list[ScenarioZONT] = []
    car_state: CarStateZONT = []
    device_info: DeviceInfoZONT = []

    @validator('guard_zones')
    def guard_zones_should_be_list(
        cls, v: list[GuardZoneZONT] | GuardZoneZONT
    ) -> list[GuardZoneZONT]:
        if isinstance(v, GuardZoneZONT):
            return [v]
        return v


class AccountZont(BaseModel):
    """Общий класс всех устройств"""

    devices: list[DeviceZONT]
    ok: bool


class TokenZont(BaseModel):
    """Клас ответа получения токена"""

    token: str
    token_id: str
    ok: bool


class ErrorZont(BaseModel):
    """Клас ответа об ошибке"""

    ok: bool
    error: str
    error_ui: str
