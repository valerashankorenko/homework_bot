# Бот - ассистент

## О проекте

 - Раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы.
 - При обновлении статуса анализирует ответ API и отправляет вам соответствующее уведомление в Telegram.
 - Логгирует свою работу и сообщает вам о важных проблемах сообщением в Telegram.

## Автор проекта:
Валерий Шанкоренко<br/>
Github: [Valera Shankorenko](https://github.com/valerashankorenko)<br/>
Telegram:[@valeron007](https://t.me/valeron007)<br/>
E-mail:valerashankorenko@yandex.by<br/>

## Стек технологий
- [Python](https://www.python.org/)
- [Python-telegram-bot](https://python-telegram-bot.org/)


## Как запустить проект:
1. Клонировать репозиторий:
```shell
git clone git@github.com:valerashankorenko/homework_bot.git
```
2. Перейти в папку с проектом:
```shell
cd homework_bot/
```
3. Установить виртуальное окружение для проекта:
```shell
python -m venv venv
```
4. Активировать виртуальное окружение для проекта:
```shell
# для OS Lunix и MacOS
source venv/bin/activate

# для OS Windows
source venv/Scripts/activate
```
5. Установить зависимости:
```shell
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
6. Выполнить миграции на уровне проекта:
```shell
python3 manage.py makemigrations
python3 manage.py migrate
```
7. Зарегистрировать чат-бота в Телеграм

8. Создать в корневой директории файл .env для хранения переменных окружения
```
PRAKTIKUM_TOKEN = 'xxx'
TELEGRAM_TOKEN = 'xxx'
TELEGRAM_CHAT_ID = 'xxx'
```
9.Запустить проект локально:
```shell
# для OS Lunix и MacOS
python3 homework_bot.py

# для OS Windows
python homework_bot.py
```
Пример ответа бота - ассистента:
```
{
   "homeworks":[
      {
         "id":123,
         "status":"approved",
         "homework_name":"valerashankorenko__homework_bot-master.zip",
         "reviewer_comment":"Всё нравится",
         "date_updated":"2023-12-14T14:40:57Z",
         "lesson_name":"Итоговый проект"
      }
   ],
   "current_date":1581804979
}
```
