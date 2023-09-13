import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': 0}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)


class HomeworkStatusError(Exception):
    """
    Исключение, возникающее при проблемах со статусом домашнего задания.

    Это исключение следует использовать, когда домашнее задание
    находится в неопределенном, недопустимом или противоречивом состоянии,
    что нарушает нормальную работу программы.
    """

    pass


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_variables = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = False
    for token in env_variables:
        value = os.getenv(token)
        if value:
            print(f'{token} доступен. Значение: {value}')
        else:
            print(f'{token} отсутствует или не доступен.')
            missing_vars = True

    return not missing_vars


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logging.debug(f'Сообщение успешно отправлено в Telegram: {message}')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API сервиса Практикум.Домашка."""
    params = {'timestamp': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params={**PAYLOAD, **params})
        if homework_statuses.status_code != 200:
            raise Exception(f'Ошибка при запросе к API.'
                            f'Код статуса: {homework_statuses.status_code}')
        response = homework_statuses.json()
        pprint(homework_statuses.json())
        if 'homeworks' in response:
            return response
        else:
            raise Exception('Отсутствует ключ "homeworks" в ответе API')
    except requests.exceptions.RequestException as error:
        raise Exception(f'Ошибка при запросе к API: {error}')
    except Exception as error:
        raise Exception(f'Произошла непредвиденная ошибка: {error}')


def check_response(response):
    """
    Проверка ответа API на соответствие документации.
    из урока API сервиса Практикум.Домашка.
    """
    if not isinstance(response, dict):
        raise TypeError('Некорректный формат ответа API')
    expected_keys = ['current_date', 'homeworks']
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
        logging.error(message)
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Ключ status недоступен'
        logging.error(message)
        raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Статус домашки не найден в базе статусов.')
        raise HomeworkStatusError('Неизвестный статус в ответе API')


def main():
    """Основная логика работы бота."""
    if TELEGRAM_TOKEN is None:
        logging.critical('Отсутствуют обязательные переменные окружения.')
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    new_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.info('Статус не обновлен.')
            elif new_status != homeworks[0]['status']:
                message = parse_status(homeworks[0])
                try:
                    send_message(bot, message)
                    logging.info(f'Сообщение отправлено: {message}')
                except Exception as send_exception:
                    logging.error(f'Ошибка отправки сообщения:'
                                  f'{send_exception}')
                new_status = homeworks[0]['status']
            else:
                logging.info('Изменений нет.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
