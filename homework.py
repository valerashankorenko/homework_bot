import logging
import os
import sys
import time
from http import HTTPStatus
from json import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HomeworkStatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENV_VARIABLES = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
TIME_IN_SECONDS = 300

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def check_tokens():
    """Проверка доступности переменных окружения."""
    for token in ENV_VARIABLES:
        if globals()[token] is None:
            logging.critical(f'{token} отсутствует или не доступен.')
            exit()


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение успешно отправлено в Telegram: {message}')
        return True
    except telegram.error.TelegramError as error:
        logger.error(f'Сбой в работе программы: {error}')
        return False


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API сервиса Практикум.Домашка."""
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params={'from_date': timestamp})
    except requests.exceptions.RequestException as error:
        raise Exception(f'Ошибка при запросе к API: {error}')

    if homework_statuses.status_code == HTTPStatus.OK:
        try:
            return homework_statuses.json()
        except JSONDecodeError as error:
            raise Exception(f'Ошибка при преобразовании'
                            f'ответа сервера в JSON: {error}')

    if homework_statuses.status_code == HTTPStatus.BAD_REQUEST:
        error_message = ('Некорректный запрос:'
                         'проверьте заголовки и параметры.')
    elif homework_statuses.status_code == HTTPStatus.UNAUTHORIZED:
        error_message = 'Ошибка авторизации: проверьте API-ключ.'
    elif homework_statuses.status_code == HTTPStatus.FORBIDDEN:
        error_message = ('Доступ запрещен:'
                         'у вас нет прав для доступа к этому ресурсу.')
    elif homework_statuses.status_code == HTTPStatus.NOT_FOUND:
        error_message = ('Ресурс не найден:'
                         'проверьте правильность URL-адреса эндпоинта.')
    else:
        error_message = (f'Ошибка при запросе к API.'
                         f'Код статуса: {homework_statuses.status_code}.'
                         f'Причина: {homework_statuses.reason}')
    raise Exception(error_message)


def check_response(response):
    """
    Проверка ответа API на соответствие документации.
    из урока API сервиса Практикум.Домашка.
    """
    if not isinstance(response, dict):
        raise TypeError('Некорректный формат ответа API')

    expected_keys = ('current_date', 'homeworks')

    for key in expected_keys:
        if key not in response:
            raise TypeError(f'Отсутствует ключ "{key}" в ответе API')

    if not isinstance(response['current_date'], int):
        raise TypeError('Некорректный тип данных'
                        'для ключа "current_date" в ответе API')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Некорректный тип данных'
                        'для ключа "homeworks" в ответе API')

    return response['homeworks']


def parse_status(homework):
    """Статус домашней работы."""
    if 'homework_name' not in homework:
        message = 'Ключ homework_name недоступен'
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Ключ status недоступен'
        raise KeyError(message)

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    message = 'Статус домашней работы не найден в базе статусов.'
    raise HomeworkStatusError(message)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = (int(time.time())) - TIME_IN_SECONDS
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp - RETRY_PERIOD)
            new_timestamp = response.get('current_date', timestamp)
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)

            timestamp = new_timestamp
            last_error = None
        except Exception as error:
            logger.error(error)
            if error != last_error:
                result = send_message(bot, str(error))
                if result:
                    last_error = error
                else:
                    logger.error('Не удалось отправить сообщение в Telegram')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler('app.log', mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
