import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='program.log',
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5)
logger.addHandler(handler)


def check_tokens(tokens):
    """Проверяет доступность переменных окружения."""
    tokens = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for token in tokens:
        if os.getenv(token) is None:
            logging.CRITICAL('Отсутсвует обязательная переменная')
            print(f"Переменная {token} не установлена!")
        else:
            logging.debug('Отсутсвует обязательная переменная')
            print(f"Переменная {token} установлена.")


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        logging.info('Начало отправки сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение успешно отправлено')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в чат: {error}')


def get_api_answer(timestamp):
    """Запрос к единственному ендпоинту."""
    timestamp = timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        error_message = f'Ошибка при запросе к основному API: {error}'
        logging.error(error_message)
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            error_message = (
                f'Ошибка при запросе к API.'
                f'Статус-код API: {homework_statuses.status_code}.'
            )
            logging.error(error_message)
            raise RequestException(error_message)
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        error_message = 'Ответ от API имеет некорректный тип.'
        logging.error('Ответ от API имеет некорректный тип.')
        raise TypeError(error_message)
    if 'homeworks' not in response.keys():
        error_message = 'Ответ от API не содержит ключа homeworks.'
        logging.error(error_message)
        raise KeyError(error_message)
    if not isinstance(response.get('homeworks'), list):
        error_message = 'В ответе от API приходит не словарь.'
        logging.error(error_message)
        raise TypeError(error_message)
    return response['homeworks']


def parse_status(homework):
    """Извлекает  статус домашней работы."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        logging.ERROR('Ошибка: недокументированный статус домашней работы.')
        raise KeyError('Нет такого статуса домашней работы')
    if 'homework_name' not in homework:
        logging.ERROR('Ошибка: нет нужных ключей.')
        raise KeyError('Нет таких ключей в домашней работе')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not PRACTICUM_TOKEN:
        logging.getLogger(__name__)
        logging.critical('Нет важной переменной, надо звать нетранера')
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    initial_status = ''
    initial_error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_homework = check_response(response)
            if checked_homework:
                homework_status = parse_status(checked_homework[0])
                if homework_status != initial_status:
                    send_message(bot, homework_status)
                    initial_status = homework_status
            else:
                logging.debug('В ответе нет новых статусов.')
                send_message(bot, 'В ответе нет новых статусов.')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != initial_error_message:
                send_message(bot, message)
                initial_error_message = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
