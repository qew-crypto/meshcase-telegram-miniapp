import os
import unittest
from unittest.mock import patch
from bot_greeting import handle_start


class GreetingTests(unittest.TestCase):
    def send(self, text='/start', kind='private'):
        calls = []
        handled = handle_start({'message': {'text': text, 'chat': {'id': 123, 'type': kind}}}, lambda *a: calls.append(a))
        return handled, calls

    @patch.dict(os.environ, {}, clear=True)
    def test_start(self):
        handled, calls = self.send('/start referral')
        self.assertTrue(handled)
        self.assertEqual(calls[0][0], 'sendMessage')
        self.assertEqual(calls[0][1]['chat_id'], 123)
        self.assertNotIn('parse_mode', calls[0][1])

    def test_other_messages(self):
        for text in ['', '/starter', 'hello']:
            self.assertEqual(self.send(text), (False, []))
        self.assertEqual(self.send(kind='group'), (False, []))
        self.assertFalse(handle_start({'pre_checkout_query': {}}, self.fail))

    @patch.dict(os.environ, {'MESHCASE_WELCOME_TEXT': 'Привет!', 'MESHCASE_SUPPORT_URL': 'https://t.me/support'})
    def test_configuration(self):
        payload = self.send('/start@meshbot')[1][0][1]
        self.assertEqual(payload['text'], 'Привет!')
        self.assertIn('reply_markup', payload)

    @patch.dict(os.environ, {'MESHCASE_SUPPORT_URL': 'http://example.com'})
    def test_insecure_url(self):
        self.assertNotIn('reply_markup', self.send()[1][0][1])

if __name__ == '__main__':
    unittest.main()
