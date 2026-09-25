"""Informational Telegram commands. No payment or game operations."""
import os
from urllib.parse import urlsplit


def support_url():
    url = os.environ.get('MESHCASE_SUPPORT_URL', '').strip()
    try:
        parsed = urlsplit(url)
        if (parsed.scheme == 'https' and parsed.hostname
                and not parsed.username and not parsed.password
                and not any(c.isspace() or ord(c) < 32 for c in url)):
            return url
    except ValueError:
        pass
    return None


def handle_start(update, bot_api):
    """Keep legacy entry point for the existing webhook; handle help as well."""
    if not isinstance(update, dict):
        return False
    message = update.get('message')
    if not isinstance(message, dict):
        return False
    chat = message.get('chat')
    if not isinstance(chat, dict):
        return False
    if chat.get('type') != 'private' or type(chat.get('id')) is not int:
        return False
    text = message.get('text')
    if not isinstance(text, str) or not text.split():
        return False
    command = text.split()[0].split('@', 1)[0]
    url = support_url()
    if command == '/start':
        text = os.environ.get('MESHCASE_WELCOME_TEXT', '').strip() or (
            'Привет! Добро пожаловать в MeshCase.\n\n'
            '/help — справка\n/support — связь с поддержкой')
    elif command == '/help':
        text = ('Доступные команды:\n/start — приветствие\n'
                '/support — как обратиться в поддержку\n\n'
                'Не передавайте пароли, коды входа и данные банковской карты. '
                'Сообщение этому боту само по себе не создаёт обращение.')
    elif command == '/support':
        text = os.environ.get('MESHCASE_SUPPORT_TEXT', '').strip() or (
            'Опишите проблему: что вы делали, что ожидали и что произошло. '
            'Укажите время ошибки и при необходимости приложите скриншот '
            'без личных данных. Не отправляйте пароли и коды входа.')
        text = text[:3500] + ('\n\nНажмите «Поддержка», чтобы отправить обращение.' if url else
            '\n\nКонтакт поддержки пока не настроен. Обращение не создано.')
    else:
        return False
    payload = {'chat_id': chat['id'], 'text': text[:4096]}
    if url:
        payload['reply_markup'] = {'inline_keyboard': [[{'text': 'Поддержка', 'url': url}]]}
    bot_api('sendMessage', payload)
    return True
