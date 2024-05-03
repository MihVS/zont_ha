from datetime import datetime

from pydantic import BaseModel, validator


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
    # current_mode_name: int | None = None
    target_min: float | str | None
    target_max: float | str | None


class HeatingModeZONT(ControlEntityZONT):
    """Отопительные режимы"""

    can_be_applied: bool
    color: str | None


class BoilerModeZONT(ControlEntityZONT):
    """Котловые режимы"""

    can_be_applied: bool
    color: str | None


class SensorZONT(BaseEntityZONT):
    """Сенсоры"""

    type: str
    status: str
    value: float | None = None
    unit: str | None


class OTSensorZONT(SensorZONT):
    """Сенсоры котлов"""

    boiler_adapter_id: int
    id: str


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


class DeviceZONT(BaseEntityZONT):
    """Модель контроллера"""

    model: str
    online: bool
    widget_type: str | None
    heating_circuits: list[HeatingCircuitZONT] = []
    heating_modes: list[HeatingModeZONT] | None
    boiler_modes: list[BoilerModeZONT] = []
    sensors: list[SensorZONT] = []
    ot_sensors: list[OTSensorZONT] = []
    guard_zones: list[GuardZoneZONT] | GuardZoneZONT = []
    custom_controls: list[CustomControlZONT] = []
    scenarios: list[ScenarioZONT] = []
    car_state: CarStateZONT = []

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
