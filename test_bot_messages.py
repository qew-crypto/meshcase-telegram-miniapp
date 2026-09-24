import unittest
from unittest.mock import Mock, patch
import bot_messages


class BotMessagesTests(unittest.TestCase):
    def test_start(self):
        api = Mock()
        self.assertTrue(bot_messages.welcome({'message': {'chat': {'id': 12, 'type': 'private'}, 'text': '/start referral'}}, api))
        self.assertEqual(api.call_args.args[0], 'sendMessage')
        self.assertEqual(api.call_args.args[1]['chat_id'], 12)

    def test_ignore_groups_and_other_commands(self):
        api = Mock()
        for kind, text in [('group', '/start'), ('private', '/starter'), ('private', 'hello')]:
            self.assertIsNone(bot_messages.welcome({'message': {'chat': {'id': 12, 'type': kind}, 'text': text}}, api))
        api.assert_not_called()

    def test_custom_plain_text(self):
        api = Mock()
        with patch.dict('os.environ', {'MESHCASE_WELCOME_TEXT': '<Привет>'}):
            bot_messages.welcome({'message': {'chat': {'id': 12, 'type': 'private'}, 'text': '/start'}}, api)
        self.assertEqual(api.call_args.args[1]['text'], '<Привет>')
        self.assertNotIn('parse_mode', api.call_args.args[1])

    def test_delivery_failure(self):
        api = Mock(side_effect=RuntimeError('secret URL'))
        with self.assertLogs('bot_messages', level='WARNING') as logs:
            self.assertFalse(bot_messages.send(api, 12, 'Ответ'))
        self.assertNotIn('secret URL', str(logs.output))
        self.assertFalse(bot_messages.send(None, 12, 'Ответ'))

    def test_empty_update(self):
        self.assertIsNone(bot_messages.welcome({}, Mock()))


if __name__ == '__main__':
    unittest.main()
