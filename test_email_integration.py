import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from email_filter import sender_is_authorized
from email_parser import parse_transport_email, validate_mission
from email_settings import load_imap_settings
from mission_creator import append_mission, load_missions


class EmailIntegrationTests(unittest.TestCase):
    def test_parse_and_normalize_date(self):
        mission = parse_transport_email(
            "Reference: TEST-001\nPickup: Paris\nDelivery: Lille\nDate: 10/10/2026"
        )
        self.assertEqual(mission.reference, "TEST-001")
        self.assertEqual(mission.date, "2026-10-10")
        self.assertEqual(validate_mission(mission), [])

    def test_sender_filter(self):
        rules = {
            "authorized_senders": ["dispatch@example.com"],
            "authorized_domains": ["client.test"],
        }
        self.assertTrue(sender_is_authorized("dispatch@example.com", rules))
        self.assertTrue(sender_is_authorized("ops@client.test", rules))
        self.assertFalse(sender_is_authorized("unknown@example.net", rules))

    def test_append_is_duplicate_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "missions.csv"
            mission = parse_transport_email(
                "Reference: TEST-002\nPickup: Paris\nDelivery: Lyon\nDate: 2026-10-11"
            )
            self.assertTrue(append_mission(path, mission))
            self.assertFalse(append_mission(path, mission))
            self.assertEqual(len(load_missions(path)), 1)

    def test_gmail_preset(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "config").mkdir()
            (base / "config" / "mailbox.json").write_text(
                '{"provider":"gmail","user":"transport@example.com"}',
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"MAMOURART_IMAP_PASSWORD": "secret"}, clear=True):
                settings = load_imap_settings(base)
            self.assertEqual(settings.host, "imap.gmail.com")
            self.assertEqual(settings.port, 993)

    def test_outlook_password_auth_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "config").mkdir()
            (base / "config" / "mailbox.json").write_text(
                '{"provider":"outlook","user":"transport@example.com"}',
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"MAMOURART_IMAP_PASSWORD": "secret"}, clear=True):
                with self.assertRaises(RuntimeError):
                    load_imap_settings(base)


if __name__ == "__main__":
    unittest.main()
