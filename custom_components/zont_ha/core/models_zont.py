from pydantic import BaseModel


class BaseEntityZONT(BaseModel):
    """Базовая модель сущностей контроллера"""

    id: int
    name: str


class ControlEntityZONT(BaseEntityZONT):
    """Базовая модель для управляемых сущностей"""
    pass


class HeatingCircuit(ControlEntityZONT):
    """Контур отопления"""

    status: str
    active: bool
    actual_temp: float | None
    is_off: bool
    target_temp: float | None
    current_mode: int | None
    current_mode_name: int | None = None
    target_min: float | None
    target_max: float | None


class HeatingMode(ControlEntityZONT):
    """Отопительные режимы"""

    can_be_applied: bool
    color: str | None


class Sensor(BaseEntityZONT):
    """Сенсоры"""

    type: str
    status: str
    value: float | None
    unit: str


class GuardZone(ControlEntityZONT):
    """Охранная зона"""

    state: str
    alarm: bool


class CustomControl(ControlEntityZONT):
    """Пользовательский элемент управления"""

    name: dict | str
    type: str
    status: bool | None = None


class Scenario(ControlEntityZONT):
    """Сценарий"""

    pass


class Device(BaseEntityZONT):
    """Модель контроллера"""

    model: str
    online: bool
    widget_type: str
    heating_circuits: list[HeatingCircuit]
    heating_modes: list[HeatingMode]
    sensors: list[Sensor]
    guard_zones: list[GuardZone] | None
    custom_controls: list[CustomControl] | None
    scenarios: list[Scenario] | None


class Zont(BaseModel):
    """Общий класс всех устройств"""

    devices: list[Device]
    ok: bool
