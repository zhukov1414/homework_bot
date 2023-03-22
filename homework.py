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
    tokens = ({'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
                'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID})
    missing_tokens = []
    for token, value in tokens.items():
        if not value:
            missing_tokens.append(token)
            logging.critical(f'Критическая ошибка, нет {token}')
    if missing_tokens:
        logging.critical('Не хватает следующих переменных в .env: ' + ', '.join(missing_tokens))
        raise SystemExit()
    return True



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
    timestamp = int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        error_message = f'Ошибка при запросе к основному API: {error}'
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            error_message = (
                f'Ошибка при запросе к API.'
                f'Статус-код API: {homework_statuses.status_code}.'
            )
            raise RequestException(error_message)
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API имеет некорректный тип.')
    if 'homeworks' not in response.keys():
        raise KeyError('Ответ от API не содержит ключа homeworks.')
    homeworks = response['homeworks']
    if not all(isinstance(hw, dict) for hw in homeworks):
        raise TypeError('Значение ключа homeworks в ответе'
                        'от API не является списком словарей.')
    if not isinstance(homeworks, list):
        raise TypeError('В ответе от API приходит не словарь.')
    if 'current_date' not in response.keys():
        raise KeyError('Ответ от API не содержит ключа current_date.')
    return homeworks


def parse_status(homework):
    """Извлекает состояние домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ошибка: нет нужных ключей.')
    if 'status' not in homework:
        raise KeyError('Ошибка: нет нужных ключей.')
    homework_status = homework['status']
    homework_name = homework['homework_name']
    if homework_status not in HOMEWORK_VERDICTS.keys():
        raise KeyError('Ошибка: недокументированный статус домашней работы.')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens(1):
        logging.error('Нет проверки токенов')
        sys.exit()
    while True:
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            timestamp = int(time.time())
            initial_status = ''
            initial_error_message = ''
            response = get_api_answer(timestamp)
            checked_homework = check_response(response)
            if checked_homework:
                homework_status = parse_status(checked_homework[0])
                if homework_status != initial_status:
                    send_message(bot, homework_status)
                    initial_status = homework_status
            else:
                logging.debug('В ответе нет новых статусов.')
                send_message(bot, 'В ответе нет новых статусов.')
            timestamp = response['current_date']
        except (Exception, TypeError, KeyError, RequestException) as error:
            logger.exception('Произошло исключение: %s', error)
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != initial_error_message:
                send_message(bot, message)
                initial_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
