import logging
import os
import time
import sys

import requests
from dotenv import load_dotenv
from http import HTTPStatus
from telegram import TelegramError

import telegram
import exceptions


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
    level=logging.INFO
)


def send_message(bot, message):
    """Отправка сообщений."""
    logging.info('Попытка отправки сообщения в Telegram')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramError:
        logging.error('Не удалось отправить сообщение')
    logging.info('удачная отправка сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Запрос к API."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise exceptions.BadEndPoint(f'недоступность эндпоинта {error}')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.BadStatus('недоступность эндпоинта (код не 200)')
    try:
        return response.json()
    except Exception as error:
        raise exceptions.NotJson(f'не преобразовываться в JSON {error}')


def check_response(response):
    """Проверка ответа API."""
    logging.info('Ответ от API получен')
    logging.info('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise TypeError('В ответе должен быть словарь')
    if "homeworks" not in response or "current_date" not in response:
        raise exceptions.EmptyResponse(
            'отсутствие ожидаемых ключей в ответе API ',
            response
        )
    homeworks_list = response.get('homeworks')
    if not isinstance(homeworks_list, list):
        raise KeyError('В ответе под ключом должен быть список')
    logging.info('Ответ прошел валидацию')
    return homeworks_list


def parse_status(homework):
    """Извлечение статуса работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутсвует ключ homework_name')
    homework_status = homework.get('status')
    if 'status' not in homework:
        raise KeyError(
            'Отсутсвует ключ status'
        )
    if homework_status not in HOMEWORK_STATUSES:
        raise ValueError(
            'недокументированный статус домашней работы в ответе API'
        )
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logging.info('старт работы бота')
    old_error = ''
    if not check_tokens():
        message = "Отсутсвтует один или несколько токенов"
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    while True:
        try:
            homeworks_list = get_api_answer(current_timestamp)
            homeworks = check_response(homeworks_list)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            current_timestamp = homeworks_list.get(
                'current_date',
                current_timestamp
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if error != old_error:
                send_message(bot, message)
                logging.error(message)
                old_error = error
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
