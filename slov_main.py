pip install python-telegram-bot==13.7
pip install psycopg2-binary  # Для работы с PostgreSQL

import logging
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import psycopg2
from psycopg2 import sql

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки подключения к базе данных
DB_HOST = 'localhost'
DB_NAME = 'company_dict'
DB_USER = 'your_db_user'
DB_PASS = 'your_db_password'

# Функция для подключения к базе данных
def connect_to_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я Словарь компании. Используйте команды /search, /add, /edit, /delete для работы со словарем.')

# Команда /search
def search(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text('Пожалуйста, укажите термин для поиска.')
        return

    term = ' '.join(context.args)
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("SELECT definition FROM terms WHERE term = %s", (term,))
    result = cur.fetchone()

    if result:
        update.message.reply_text(f'{term}: {result[0]}')
    else:
        update.message.reply_text(f'Термин "{term}" не найден.')

    cur.close()
    conn.close()

# Команда /add
def add_term(update: Update, context: CallbackContext) -> None:
    if not context.args or len(context.args) < 2:
        update.message.reply_text('Использование: /add <термин> <определение>')
        return

    term = context.args[0]
    definition = ' '.join(context.args[1:])

    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO terms (term, definition, approved) VALUES (%s, %s, FALSE) RETURNING id", (term, definition))
    term_id = cur.fetchone()[0]

    cur.close()
    conn.commit()
    conn.close()

    update.message.reply_text(f'Термин "{term}" добавлен на модерацию. ID: {term_id}')

# Команда /edit
def edit_term(update: Update, context: CallbackContext) -> None:
    if not context.args or len(context.args) < 3:
        update.message.reply_text('Использование: /edit <ID> <новый_термин> <новое_определение>')
        return

    term_id = context.args[0]
    new_term = context.args[1]
    new_definition = ' '.join(context.args[2:])

    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("UPDATE terms SET term = %s, definition = %s WHERE id = %s AND approved = TRUE", (new_term, new_definition, term_id))

    if cur.rowcount == 0:
        update.message.reply_text('Ошибка: Термин не найден или вы не имеете права его редактировать.')
    else:
        update.message.reply_text(f'Термин с ID {term_id} успешно отредактирован.')

    cur.close()
    conn.commit()
    conn.close()

# Команда /delete
def delete_term(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text('Использование: /delete <ID>')
        return

    term_id = context.args[0]

    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM terms WHERE id = %s AND approved = TRUE", (term_id,))

    if cur.rowcount == 0:
        update.message.reply_text('Ошибка: Термин не найден или вы не имеете права его удалить.')
    else:
        update.message.reply_text(f'Термин с ID {term_id} успешно удален.')

    cur.close()
    conn.commit()
    conn.close()

# Обработка ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Обновление "%s" вызвало ошибку "%s"', update, context.error)

# Основная функция
def main() -> None:
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("search", search))
    dispatcher.add_handler(CommandHandler("add", add_term))
    dispatcher.add_handler(CommandHandler("edit", edit_term))
    dispatcher.add_handler(CommandHandler("delete", delete_term))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()