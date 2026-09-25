import os
import unittest
from unittest.mock import patch
from bot_greeting import handle_start


@patch.dict(os.environ, {}, clear=True)
class SupportCommandTests(unittest.TestCase):
    def send(self, text):
        calls = []
        result = handle_start({'message': {'chat': {'id': 123, 'type': 'private'}, 'text': text}}, lambda *args: calls.append(args))
        self.assertTrue(result)
        self.assertEqual(len(calls), 1)
        return calls[0][1]

    def test_help(self):
        self.assertIn('/support', self.send('/help')['text'])

    def test_missing_contact(self):
        payload = self.send('/support')
        self.assertIn('Обращение не создано', payload['text'])
        self.assertNotIn('reply_markup', payload)

    def test_contact(self):
        with patch.dict(os.environ, {'MESHCASE_SUPPORT_URL': 'https://t.me/example'}):
            payload = self.send('/support')
        self.assertIn('reply_markup', payload)
        self.assertIn('Нажмите', payload['text'])

    def test_bad_urls(self):
        for url in ['https://[', 'javascript:alert(1)', 'https://user:pass@example.com', 'https://example.com/\nx']:
            with self.subTest(url=url), patch.dict(os.environ, {'MESHCASE_SUPPORT_URL': url}):
                self.assertNotIn('reply_markup', self.send('/support'))

    def test_malformed_updates(self):
        for update in [None, [], {'message': []}, {'message': {'chat': []}}, {'message': {'chat': {'id': True, 'type': 'private'}, 'text': '/help'}}]:
            self.assertFalse(handle_start(update, self.fail))

    def test_lengths(self):
        with patch.dict(os.environ, {'MESHCASE_SUPPORT_TEXT': 'я' * 5000}):
            self.assertLessEqual(len(self.send('/support')['text']), 4096)

    def test_api_failure_is_not_swallowed(self):
        def fail(*args):
            raise RuntimeError('unavailable')
        with self.assertRaises(RuntimeError):
            handle_start({'message': {'chat': {'id': 123, 'type': 'private'}, 'text': '/help'}}, fail)


if __name__ == '__main__':
    unittest.main()
