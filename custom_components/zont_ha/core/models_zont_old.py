from pydantic import BaseModel, validator, root_validator


class StationaryLocationZontOld(BaseModel):
    """Модель локации устройства"""

    loc: list
    latitude: float | None
    longitude: float | None

    @root_validator
    def add_fild_latitude_longitude(cls, values):
        return {
            'longitude': values['loc'][0],
            'latitude': values['loc'][1]
        }


class HardwareType(BaseModel):
    """Модель версии платы"""

    name: str
    code: str


class Z3kZontOld(BaseModel):
    """Модель конфигурации z3k"""

    pass


class DeviceZontOld(BaseModel):
    """Модель контроллера"""

    id: int
    serial: str
    name: str
    widget_type: str
    appliance_type: str
    tempstep: float = 0.1
    firmware_version: list
    hardware_type: HardwareType
    serial: str
    stationary_location: StationaryLocationZontOld | None
    z3k_config: Z3kZontOld | None

    @validator('firmware_version')
    def firmware_version_get_first_element(cls, v: list[int]) -> int | None:
        return v[0] if len(v) else None


class AccountZontOld(BaseModel):
    """Общий класс всех устройств"""

    devices: list[DeviceZontOld]
    ok: bool
