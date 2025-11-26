import datetime

from pydantic import BaseModel


class Coordinates(BaseModel):
    """Коордианты события (для ZTC)."""

    lat: any
    lng: any


class AdditionalInfo(BaseModel):
    """Дополнительная информация объекта."""

    object_id: str | int


class DeviceEventWebhook(BaseModel):
    """Объект с информацией о событии прибора."""

    device_id: int
    device_name: str
    type: str
    title: str
    details: str
    time: datetime
    important: bool
    source: str
    gps: Coordinates
    additional_info: AdditionalInfo
