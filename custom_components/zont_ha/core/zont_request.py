import asyncio
import logging

from aiohttp import ClientConnectorError, ClientError

from ..const import ZONT_API_URLS

_LOGGER = logging.getLogger(__name__)


class ZontRequestManager:
    """Класс для управления запросами к актуальным endpoint api ZONT."""

    def __init__(self, session):
        self._session = session
        self._base_urls = ZONT_API_URLS
        self._last_base_url = ZONT_API_URLS[0]

    @staticmethod
    def _build_url(base_url: str, path: str) -> str:
        return f'{base_url}{path}'

    def _ordered_urls(self) -> list[str]:
        urls = self._base_urls.copy()
        if self._last_base_url != self._base_urls[0]:
            urls.remove(self._last_base_url)
            urls.insert(0, self._last_base_url)
        return urls

    async def request(
            self, method: str, path: str, idempotent: bool | None = None,
            **kwargs):
        """Запрос к API ZONT с переключением на запасные адреса.

        Команду (POST) на другой адрес повторяем, только если соединение
        не установилось: после таймаута или 5xx она могла выполниться,
        и повтор сработал бы дважды. Чтение через POST помечается
        idempotent=True.
        """
        if idempotent is None:
            idempotent = method == 'GET'
        last_exc = None

        for base_url in self._ordered_urls():
            url = self._build_url(base_url, path)
            _LOGGER.debug(f'Request {method} {url}')
            try:
                resp = await self._session.request(method, url, **kwargs)
            except ClientConnectorError as e:
                _LOGGER.warning(f'Could not connect to {base_url}: {e}')
                last_exc = e
                continue
            except (asyncio.TimeoutError, ClientError) as e:
                if not idempotent:
                    raise
                _LOGGER.warning(f'Request failed for {base_url}: {e!r}')
                last_exc = e
                continue

            if resp.status < 500 or not idempotent:
                if base_url != self._last_base_url:
                    _LOGGER.info(f'Switching API endpoint to {base_url}')
                self._last_base_url = base_url
                return resp

            _LOGGER.warning(f'Server error {resp.status} on {base_url}')
            resp.release()

        raise last_exc or ClientError('All API endpoints failed')
