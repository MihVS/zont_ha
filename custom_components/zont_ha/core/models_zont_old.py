from pydantic import BaseModel, validator


class Coordinate(BaseModel):
    """Модель координат устройства"""

    latitude: float
    longitude: float


class StationaryLocationZontOld(BaseModel):
    """Модель локации устройства"""

    loc: list

    @validator('loc')
    def loc_get_latitude_longitude(cls, v: list[int]) -> Coordinate:
        coordinate = Coordinate.parse_obj(
            {'latitude': v[0], 'longitude': v[1]}
        )
        return coordinate


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
    appliance_type: str
    tempstep: int | float = 0.1
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
