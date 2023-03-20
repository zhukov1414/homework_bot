import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import sys
load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


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
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN, 'TELEGRAM_TOKEN': TELEGRAM_TOKEN, 'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID}
    for token, value in tokens.items():
        print(token)
        print(value)
        if value is None:
            logging.critical('Критическая ошибка,'
                             f'нет {token} позовем нетранера')
            sys.exit()
    return token

check_tokens(1)
"""     tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for token in tokens:
        if token is None:
            logging.critical('Критическая ошибка,'
                             'позовем нетранера')
            raise TypeError('Нет нужных переменных')

check_tokens(1) """


"""     tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for token in tokens:
        if token is None:
            logging.critical('Критическая ошибка,'
                             'позовем нетранера')
            raise TypeError('Нет нужных переменных') """