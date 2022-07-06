class NotJson(Exception):
    """не преобразовываться в JSON"""

    pass

class BadEndPoint(Exception):
    """Ошибка в Endpoint"""

    pass

class BadStatus(Exception):
    """Статус код не равен 200"""

    pass

class EmptyResponse(KeyError):
    '''Отсутсвуют необходимые ключи в ответе'''

    pass