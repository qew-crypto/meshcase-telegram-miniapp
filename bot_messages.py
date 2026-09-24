"""Non-commercial bot greetings and support notifications."""
import logging
import os

log = logging.getLogger(__name__)


def send(bot_api, chat_id, text):
    if bot_api is None:
        return False
    try:
        bot_api('sendMessage', {'chat_id': chat_id, 'text': text[:4096]})
        return True
    except Exception:
        # Do not log exception URLs: they can contain the bot token.
        log.warning('Telegram support notification could not be delivered')
        return False


def welcome(update, bot_api):
    message = update.get('message') or {}
    chat = message.get('chat') or {}
    text = message.get('text') or ''
    if not isinstance(text, str) or chat.get('type') != 'private':
        return None
    command = text.split(maxsplit=1)[0] if text.strip() else ''
    if command.split('@')[0] != '/start' or not chat.get('id'):
        return None
    greeting = os.environ.get('MESHCASE_WELCOME_TEXT', '').strip() or (
        'Привет! Добро пожаловать в MeshCase.\n\n'
        'Если нужна помощь, создайте обращение в разделе «Поддержка» приложения. '
        'Ответ поддержки придёт сюда.\n\n'
        'Никому не сообщайте коды входа в Telegram и пароли: поддержка их не запрашивает.'
    )
    return send(bot_api, chat['id'], greeting)
