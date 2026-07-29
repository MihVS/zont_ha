from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .core.models_zont_v3 import (
    AdapterZONT, DeviceZONT, OpenThermValueZONT
)

ADAPTER_STATUS_FLAGS = (
    ('ch', 'Отопление: запрос тепла'),
    ('dhw', 'ГВС: запрос тепла'),
    ('fl', 'Котёл: работа'),
)


class ZontAdapterStatusBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Бинарный сенсор флага состояния адаптера цифровой шины."""

    def __init__(
            self, coordinator: ZontCoordinator, device: DeviceZONT,
            adapter: AdapterZONT, flag: str, name: str, unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._adapter = adapter
        self._flag = flag
        self._name = name
        self._unique_id = unique_id
        self._adapter_available = True
        self._attr_device_info = coordinator.devices_info(device.id)

    @property
    def name(self) -> str:
        return f'{self._device.name}_{self._name}'

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        return super().available and self._adapter_available

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        if self._flag == 'ch':
            return BinarySensorDeviceClass.HEAT
        return None

    @property
    def is_on(self) -> bool | None:
        status = self._get_status()
        if status is None or not isinstance(status.value, bool):
            return None
        return status.value

    def _get_status(self) -> OpenThermValueZONT | None:
        if self._adapter.status is None:
            return None
        return next(
            (status for status in self._adapter.status
             if status.flag == self._flag),
            None
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обновить флаг из последнего ответа API ZONT."""
        adapter = self.coordinator.zont.get_adapter(
            self._device.id, self._adapter.id
        )
        self._adapter_available = adapter is not None
        if adapter is not None:
            self._adapter = adapter
        self.async_write_ha_state()
