"""Restart tests without a running Home Assistant (aiohttp and pydantic 2)."""

import asyncio
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

from aiohttp import ClientTimeout


def load_integration():
    """Load the real client/button modules with only the HA boundary stubbed."""
    class HomeAssistantError(Exception):
        pass

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator
            self.hass = None

    package = ModuleType('_zont_restart_tests')
    package.__path__ = [str(
        Path(__file__).parents[1] / 'custom_components' / 'zont_ha'
    )]
    package.ZontCoordinator = type('ZontCoordinator', (), {})

    ha_const = MagicMock()
    ha_const.EntityCategory.CONFIG = 'config'
    modules = {
        '_zont_restart_tests': package,
        'homeassistant': ModuleType('homeassistant'),
        'homeassistant.components': ModuleType('homeassistant.components'),
        'homeassistant.components.alarm_control_panel': ModuleType('alarm'),
        'homeassistant.components.alarm_control_panel.const': MagicMock(),
        'homeassistant.components.button': SimpleNamespace(
            ButtonEntity=type('ButtonEntity', (), {}),
            ButtonDeviceClass=SimpleNamespace(RESTART='restart'),
        ),
        'homeassistant.config_entries': SimpleNamespace(ConfigEntry=object),
        'homeassistant.const': ha_const,
        'homeassistant.core': SimpleNamespace(HomeAssistant=object),
        'homeassistant.exceptions': SimpleNamespace(
            HomeAssistantError=HomeAssistantError
        ),
        'homeassistant.helpers': ModuleType('homeassistant.helpers'),
        'homeassistant.helpers.aiohttp_client': MagicMock(),
        'homeassistant.helpers.entity_platform': SimpleNamespace(
            AddEntitiesCallback=object
        ),
        'homeassistant.helpers.update_coordinator': SimpleNamespace(
            CoordinatorEntity=CoordinatorEntity
        ),
    }
    with patch.dict(sys.modules, modules):
        client = importlib.import_module('_zont_restart_tests.core.zont')
        button = importlib.import_module('_zont_restart_tests.button')
    return client, button


client_module, button_module = load_integration()
Zont = client_module.Zont
ResponseZontError = client_module.ResponseZontError


class RestartFixture:
    def setUp(self):
        self.device = SimpleNamespace(
            id=1001, name='Controller', online=True, controls=None, modes=[],
            circuits=[], actuators=None,
        )
        self.legacy = SimpleNamespace(id=self.device.id, z3k_config={})
        self.response = SimpleNamespace(
            status=200, json=AsyncMock(return_value={'ok': True})
        )
        self.zont = Zont.__new__(Zont)
        self.zont.headers = {'X-ZONT-Token': 'test-token'}
        self.zont.data = SimpleNamespace(devices=[self.device])
        self.zont.data_old = SimpleNamespace(devices=[self.legacy])
        self.zont.manager = SimpleNamespace(
            request=AsyncMock(return_value=self.response)
        )


class ControllerRestartTests(RestartFixture, unittest.IsolatedAsyncioTestCase):
    async def test_authenticated_restart_has_no_deferred_delivery(self):
        await self.zont.restart_controller(device=self.device)

        self.zont.manager.request.assert_awaited_once_with(
            method='POST',
            path='api/send_z3k_command',
            headers=self.zont.headers,
            timeout=ANY,
            idempotent=False,
            json={
                'device_id': 1001,
                'command_name': 'RestartDevice',
                'object_id': 0,
                'request_time': 1000,
                'command_args': None,
                'is_guaranteed': False,
            },
        )
        timeout = self.zont.manager.request.call_args.kwargs['timeout']
        self.assertIsInstance(timeout, ClientTimeout)
        self.assertEqual(timeout.total, 30)

    async def test_uses_current_online_state_instead_of_cached_device(self):
        self.zont.data.devices = [SimpleNamespace(id=1001, online=False)]
        with self.assertRaises(ResponseZontError):
            await self.zont.restart_controller(device=self.device)
        self.zont.manager.request.assert_not_awaited()

    async def test_removed_device_is_not_restarted(self):
        self.zont.data.devices = []
        with self.assertRaises(ResponseZontError):
            await self.zont.restart_controller(device=self.device)
        self.zont.manager.request.assert_not_awaited()

    async def test_non_z3k_and_missing_legacy_metadata_are_rejected(self):
        for devices in [[SimpleNamespace(id=1001, z3k_config=None)], []]:
            with self.subTest(devices=devices):
                self.zont.data_old.devices = devices
                with self.assertRaises(ResponseZontError):
                    await self.zont.restart_controller(device=self.device)
                self.zont.manager.request.assert_not_awaited()

    async def test_http_and_api_rejections_are_not_retried(self):
        for status, body in [
            (403, {'ok': False}), (500, {'ok': False}),
            (200, {'ok': False, 'error': 'timeout'}), (200, {'ok': 1}),
            (200, None), (200, []),
        ]:
            with self.subTest(status=status, body=body):
                self.response.status = status
                self.response.json.return_value = body
                self.zont.manager.request.reset_mock()
                with self.assertRaises(ResponseZontError):
                    await self.zont.restart_controller(device=self.device)
                self.zont.manager.request.assert_awaited_once()

    async def test_non_json_response_is_reported(self):
        self.response.json.side_effect = ValueError('invalid JSON')
        with self.assertRaises(ResponseZontError):
            await self.zont.restart_controller(device=self.device)
        self.zont.manager.request.assert_awaited_once()

    async def test_ambiguous_timeout_is_not_retried(self):
        self.zont.manager.request.side_effect = asyncio.TimeoutError
        with self.assertRaises(asyncio.TimeoutError):
            await self.zont.restart_controller(device=self.device)
        self.zont.manager.request.assert_awaited_once()


class RestartButtonTests(RestartFixture, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.entry_id = 'test-entry'
        self.coordinator = SimpleNamespace(
            zont=self.zont, devices_info=Mock(return_value={})
        )
        self.hass = SimpleNamespace(data={button_module.DOMAIN: {
            button_module.ENTRIES: {self.entry_id: self.coordinator},
            button_module.CURRENT_ENTITY_IDS: {self.entry_id: []},
        }})

    async def setup_buttons(self):
        added = []
        await button_module.async_setup_entry(
            self.hass, SimpleNamespace(entry_id=self.entry_id), added.extend
        )
        return added

    async def test_discovery_preserves_existing_buttons_and_unique_ids(self):
        self.device.controls = SimpleNamespace(buttons=[
            SimpleNamespace(id=7, name='Relay')
        ])
        self.device.modes = [SimpleNamespace(id=8, name='Комфорт')]
        added = await self.setup_buttons()
        self.assertEqual(len(added), 3)
        restart = next(b for b in added if isinstance(
            b, button_module.ZontRestartController
        ))
        self.assertEqual(restart.unique_id, 'test-entry1001_restart_controller')
        self.assertFalse(restart._attr_entity_registry_enabled_default)
        self.assertEqual(restart._attr_entity_category, 'config')
        self.assertEqual(restart._attr_device_class, 'restart')
        registered = self.hass.data[button_module.DOMAIN][
            button_module.CURRENT_ENTITY_IDS
        ][self.entry_id]
        self.assertCountEqual(registered, [b.unique_id for b in added])

    async def test_button_is_not_created_without_z3k_config(self):
        for devices in [[SimpleNamespace(id=1001, z3k_config=None)], []]:
            with self.subTest(devices=devices):
                self.zont.data_old.devices = devices
                self.assertEqual(await self.setup_buttons(), [])

    async def test_button_calls_the_existing_client(self):
        restart, = await self.setup_buttons()
        self.zont.restart_controller = AsyncMock()
        await restart.async_press()
        self.zont.restart_controller.assert_awaited_once_with(device=self.device)

    async def test_diagnostics_follow_current_device(self):
        restart, = await self.setup_buttons()
        circuit = SimpleNamespace(model_dump=Mock(return_value={'id': 2}))
        actuator = SimpleNamespace(model_dump=Mock(return_value={'adapters': []}))
        self.zont.data.devices = [SimpleNamespace(
            id=1001, circuits=[circuit], actuators=actuator
        )]
        self.assertEqual(restart.extra_state_attributes, {
            'controller_id': 1001, 'circuits': [{'id': 2}],
            'actuators': {'adapters': []},
        })
        circuit.model_dump.assert_called_once_with(mode='json')
        actuator.model_dump.assert_called_once_with(mode='json')
        self.zont.data.devices = []
        self.assertEqual(restart.extra_state_attributes, {})


if __name__ == '__main__':
    unittest.main()
