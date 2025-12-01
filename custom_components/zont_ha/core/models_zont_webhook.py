from pydantic import BaseModel


class Coordinates(BaseModel):
    """Коордианты события (для ZTC)."""

    lat: str
    lng: str


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
    time: str
    important: bool
    source: str
    gps: Coordinates
    additional_info: AdditionalInfo
