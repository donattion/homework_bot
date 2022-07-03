import logging
import os
import time


import requests
from dotenv import load_dotenv

import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s - %(lineno)s",
    level=logging.DEBUG
)


def send_message(bot, message):
    """Отправка сообщений"""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('удачная отправка сообщения в Telegram')
    except:
        logging.error('сбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Запрос к API"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except:
        logging.error('недоступность эндпоинта')
    if response.status_code != 200:
        logging.error('недоступность эндпоинта (код не 200)')
    return response.json()


def check_response(response):
    """Проверка ответа API"""
    if not isinstance(response, dict):
        logging.error('Неверный тип данных у элемента response')
    elif 'homeworks' not in response:
        logging.error('отсутствие ожидаемых ключей в ответе API ')
    elif not isinstance(response['homeworks'], list):
        logging.error('Неверный тип данных у элемента homeworks')
    return response.get('homeworks')


def parse_status(homework):
    """Извлечение статуса работы"""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except:
        logging.error('недокументированный статус домашней работы, обнаруженный в ответе API')


def check_tokens():
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
    ):
        logging.critical('отсутствие обязательных переменных окружения во время запуска бота')
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    logging.debug('старт работы бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                current_homework = homeworks[0]
                lesson_name = current_homework['lesson_name']
                status = parse_status(current_homework)
                send_message(bot, f'{lesson_name}. {status}')
            else:
                logging.debug('Нет новых статусов')
                send_message(bot, 'нет новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    if check_tokens():
        main()
    else:
        SystemExit()