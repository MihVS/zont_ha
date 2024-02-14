from pydantic import BaseModel


class DeviceZontOld(BaseModel):
    """Модель контроллера"""

    id: int
    serial: str
    tempstep: int | float



class AccountZontOld(BaseModel):
    """Общий класс всех устройств"""

    devices: list[DeviceZontOld]
    ok: bool
