class RequestAPIZONTError(Exception):
    """Ошибка запроса к сервису zont-online.ru/api."""
    pass


class InvalidMail(Exception):
    """Ошибка валидации почты"""
    pass


class SensorNotFound(Exception):
    """Сенсор по заданному id не найден."""
    pass


class TemperatureOutOfRange(Exception):
    """Задана температура в пределах допустимого диапазона."""
    pass
