from typing import Any

from pydantic import BaseModel

from .enums import (
    TypeOfCircuit, TypeOfSensor, StateOfSensor, SignalOfSensor, GuardState
)


class BaseEntityZONT(BaseModel):
    """Базовая модель сущностей контроллера"""

    id: int | str
    name: str


class ControlEntityZONT(BaseEntityZONT):
    """Базовая модель для управляемых сущностей"""
    pass


class ErrorBoilerZONT(BaseModel):
    """Ошибка котла."""

    oem: str
    text: str


class CircuitZONT(ControlEntityZONT):
    """Контур отопления"""

    status: str | None
    type: TypeOfCircuit
    active: bool
    actual_temp: float | None
    is_off: bool
    target_temp: float | None
    current_mode: int | None
    in_summer_mode: bool
    min: float | None = None
    max: float | None = None
    error: ErrorBoilerZONT = None
    icon: str | None = None


class VersionZONT(BaseModel):
    """Объект с данными о версиях прибора."""

    hardware: str | None
    software: str | None


class DeviceInfoZONT(BaseModel):
    """Информация об устройстве."""

    id: str
    model: str
    serial: str
    widget_type: str | None
    version: VersionZONT


class HeatingModeZONT(ControlEntityZONT):
    """Отопительные режимы"""

    can_be_applied: list[int] = []
    applied: list[int] = []
    color: str | None = None
    icon: str | None = None


class LimitsSensorZONT(BaseModel):
    """Пределы датчика."""

    high: float | None
    low: float | None


class SensorZONT(BaseEntityZONT):
    """Сенсоры"""

    type: TypeOfSensor
    status: StateOfSensor = StateOfSensor.UNKNOWN
    value: float | str | None = None
    triggered: bool | None = None
    unit: str | None = None
    limits: LimitsSensorZONT | None = None
    battery: int | None = None
    rssi: float | None = None
    signal_strength: SignalOfSensor | None = None
    color: str | None = None
    icon: str | None = None


class GuardZoneZONT(ControlEntityZONT):
    """Охранная зона"""

    state: GuardState
    alarm: bool


class ButtonNameZONT(BaseModel):
    """Наименование статуса кнопки."""

    name: str
    active_label: str
    inactive_label: str


class ButtonZONT(ControlEntityZONT):
    """Простая пользовательская кнопка."""

    view: str | None = None
    icon: str | None = None


class ToggleButtonsZONT(ControlEntityZONT):
    """Кнопка, сохраняющая состояние."""

    name: ButtonNameZONT
    active: bool | None
    view: str | None = None
    icon: str | None = None


class RegulatorZONT(ControlEntityZONT):
    """Аналоговый регулятор (например для входа 0-10 В)."""

    value: Any
    min: Any
    max: Any
    step: Any
    unit: str
    view: str | None = None
    icon: str | None = None


class StatusZONT(ControlEntityZONT):
    """Статус входа\выхода."""

    name: ButtonNameZONT
    active: bool | None
    view: str | None = None
    icon: str | None = None


class ControlsZONT(BaseModel):
    """Пользовательский элемент управления"""

    buttons: list[ButtonZONT] = []
    regulators: list[RegulatorZONT] = []
    status: list[StatusZONT] = []
    toggle_buttons: list[ToggleButtonsZONT] = []


class SimZONT(BaseModel):
    """Информация о сим-карте."""

    tariff: str | None = None
    sim_paid_until: str | None = None
    msisdn: str | None = None
    balance: str | None = None
    limit: str | None = None
    ussd: str | None = None


class ScenarioZONT(ControlEntityZONT):
    """Сценарий"""

    pass


class RelayZONT(ControlEntityZONT):
    """Релейный выход."""

    on: bool
    failed: bool


class PumpZONT(ControlEntityZONT):
    """Насос."""

    on: bool
    summer_mode: bool


class TapZONT(ControlEntityZONT):
    """Смеситель."""

    opened: bool
    opening: bool
    idle: bool
    closing: bool
    closed: bool
    failed: bool


class AdapterZONT(ControlEntityZONT):
    """Адаптер."""

    no_connection: bool
    failed: bool
    heating: list[dict] | None = None
    dhw: list[dict] | None = None


class ActuatorsZONT(BaseModel):
    """Исполнительные устройства."""

    relays: list[RelayZONT] = []
    pumps: list[PumpZONT] = []
    taps: list[TapZONT] = []
    adapters: list[AdapterZONT] = []


class DeviceZONT(BaseEntityZONT):
    """Модель контроллера"""

    online: bool
    device_info: DeviceInfoZONT
    circuits: list[CircuitZONT] = []
    modes: list[HeatingModeZONT] = []
    sensors: list[SensorZONT] = []
    guard_zones: list[GuardZoneZONT] = []
    controls: ControlsZONT | None = None
    sim_info: SimZONT = None
    scenarios: list[ScenarioZONT] = []
    actuators: ActuatorsZONT = None

    # car_state: CarStateZONT = []


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
