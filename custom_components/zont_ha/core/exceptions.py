from homeassistant.exceptions import HomeAssistantError


class RequestAPIZONTError(Exception):
    """Ошибка запроса к сервису zont-online.ru/api."""
    pass


class InvalidMail(Exception):
    """Ошибка валидации почты"""
    pass


class SensorNotFoundError(Exception):
    """Сенсор по заданному id не найден."""
    pass


class TemperatureOutOfRangeError(HomeAssistantError):
    """Задана температура не в пределах допустимого диапазона."""
    pass


class ResponseZontError(HomeAssistantError):
    """Ошибка ответа от API zont."""
    pass


class SetHvacModeError(HomeAssistantError):
    """Ошибка изменения HVAC mode"""
    pass
