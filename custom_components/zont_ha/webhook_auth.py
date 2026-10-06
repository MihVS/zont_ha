"""Идентификатор и секрет webhook ZONT.

ZONT отправляет секретный ключ подписки в заголовке
`Authorization: Bearer <ключ>`. Сверяя его, интеграция отбрасывает запросы,
пришедшие не от ZONT.
"""
import hmac
import secrets

CONF_WEBHOOK_ID = 'webhook_id'
CONF_WEBHOOK_SECRET = 'webhook_secret'

SECRET_BYTES = 32


def legacy_webhook_id(email: str) -> str:
    """webhook_id старых версий: email без `@` и `.`.

    Нужен только при миграции — чтобы уже настроенный в ZONT адрес
    продолжил работать.
    """
    return email.replace('@', '').replace('.', '')


def generate_secret() -> str:
    return secrets.token_urlsafe(SECRET_BYTES)


def is_authorized(authorization: str | None, secret: str | None) -> bool:
    """Проверяет заголовок Authorization против секрета подписки.

    Без секрета (записи, мигрированные со старых версий) проверка
    не выполняется — как раньше.
    """
    if not secret:
        return True
    expected = f'Bearer {secret}'
    return hmac.compare_digest(
        (authorization or '').encode(), expected.encode()
    )
