class TelegramError(Exception):
    """Ошибка в Telegram"""

    pass

class BadEndPoint(Exception):
    """Ошибка в Endpoint"""

    pass

class BadStatus(Exception):
    """Статус код не равен 200"""

    pass

class EmptyResponse(Exception):
    '''Отсутсвуют необходимые ключи в ответе'''

    pass