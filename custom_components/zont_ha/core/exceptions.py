class RequestAPIZONTError(Exception):
    """Ошибка запроса к сервису zont-online.ru/api"""
    pass


class InvalidMail(Exception):
    """Ошибка валидации почты"""
    pass
