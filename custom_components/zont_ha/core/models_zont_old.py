from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class StationaryLocationZontOld(BaseModel):
    """Модель локации устройства"""

    loc: list
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @model_validator(mode='after')
    def set_coordinates_from_loc(self):
        """Устанавливает latitude и longitude из loc при создании объекта"""
        if self.loc and len(self.loc) >= 2:
            if self.longitude is None:
                self.longitude = self.loc[0]
            if self.latitude is None:
                self.latitude = self.loc[1]
        return self


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
    widget_type: str | None
    appliance_type: str | None
    tempstep: float = 0.1
    stationary_location: StationaryLocationZontOld | None
    z3k_config: Z3kZontOld | None = None


class AccountZontOld(BaseModel):
    """Общий класс всех устройств"""

    devices: list[DeviceZontOld] = []
    ok: bool = False
