"""Tests for the payload builders."""

import unittest

from qrgen.payloads import (
    Contact,
    PayloadError,
    make_contact,
    make_email,
    make_sms,
    make_text,
    make_url,
    make_wifi,
)


class TextTests(unittest.TestCase):
    def test_returns_text_unchanged(self):
        self.assertEqual(make_text("Hello, world!"), "Hello, world!")

    def test_rejects_empty_text(self):
        with self.assertRaises(PayloadError):
            make_text("")

    def test_rejects_blank_text(self):
        with self.assertRaises(PayloadError):
            make_text("   ")


class UrlTests(unittest.TestCase):
    def test_adds_https_scheme(self):
        self.assertEqual(make_url("example.com"), "https://example.com")

    def test_keeps_existing_scheme(self):
        url = "http://example.com/path?q=1"
        self.assertEqual(make_url(url), url)

    def test_trims_whitespace(self):
        self.assertEqual(make_url("  https://example.com  "), "https://example.com")

    def test_rejects_empty_url(self):
        with self.assertRaises(PayloadError):
            make_url("")

    def test_rejects_unsupported_scheme(self):
        with self.assertRaises(PayloadError):
            make_url("ftp://example.com")

    def test_rejects_missing_host(self):
        with self.assertRaises(PayloadError):
            make_url("https://")

    def test_rejects_whitespace_inside_url(self):
        with self.assertRaises(PayloadError):
            make_url("example.com/a b")


class ContactTests(unittest.TestCase):
    def test_full_vcard(self):
        payload = make_contact(
            name="Ada Lovelace",
            phone="+44 20 7946 0958",
            email="ada@example.com",
            organization="Analytical Engines",
            title="Mathematician",
            address="12 St James's Square, London",
            website="example.com",
            note="First programmer",
        )
        self.assertTrue(payload.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n"))
        self.assertTrue(payload.endswith("END:VCARD\r\n"))
        self.assertIn("FN:Ada Lovelace\r\n", payload)
        self.assertIn("TEL;TYPE=CELL:+44 20 7946 0958\r\n", payload)
        self.assertIn("EMAIL;TYPE=INTERNET:ada@example.com\r\n", payload)
        self.assertIn("ORG:Analytical Engines\r\n", payload)
        self.assertIn("TITLE:Mathematician\r\n", payload)
        self.assertIn("URL:https://example.com\r\n", payload)
        self.assertIn("NOTE:First programmer\r\n", payload)

    def test_escapes_special_characters(self):
        payload = Contact(name="Doe; John, Jr.\nBack\\slash").to_vcard()
        self.assertIn("FN:Doe\\; John\\, Jr.\\nBack\\\\slash", payload)

    def test_name_is_required(self):
        with self.assertRaises(PayloadError):
            Contact(name="").to_vcard()


class EmailTests(unittest.TestCase):
    def test_plain_address(self):
        self.assertEqual(make_email("ada@example.com"), "mailto:ada@example.com")

    def test_subject_and_body_are_encoded(self):
        payload = make_email("ada@example.com", subject="Hello World", body="Line 1\nLine 2")
        self.assertEqual(
            payload,
            "mailto:ada@example.com?subject=Hello%20World&body=Line%201%0ALine%202",
        )

    def test_rejects_invalid_address(self):
        with self.assertRaises(PayloadError):
            make_email("not-an-address")


class SmsTests(unittest.TestCase):
    def test_message(self):
        self.assertEqual(
            make_sms("+15551234567", "Hello there"),
            "SMSTO:+15551234567:Hello there",
        )

    def test_without_message(self):
        self.assertEqual(make_sms("+15551234567"), "SMSTO:+15551234567")

    def test_phone_is_required(self):
        with self.assertRaises(PayloadError):
            make_sms("")


class WifiTests(unittest.TestCase):
    def test_wpa_network(self):
        self.assertEqual(
            make_wifi("MyNetwork", "secret"),
            "WIFI:T:WPA;S:MyNetwork;P:secret;;",
        )

    def test_hidden_network(self):
        self.assertEqual(
            make_wifi("MyNetwork", "secret", hidden=True),
            "WIFI:T:WPA;S:MyNetwork;P:secret;H:true;;",
        )

    def test_open_network(self):
        self.assertEqual(
            make_wifi("Cafe", security="nopass"),
            "WIFI:T:NOPASS;S:Cafe;P:;;",
        )

    def test_open_network_rejects_password(self):
        with self.assertRaises(PayloadError):
            make_wifi("Cafe", "secret", security="nopass")

    def test_escapes_special_characters(self):
        self.assertEqual(
            make_wifi("My;Net", "pa:ss,word"),
            "WIFI:T:WPA;S:My\\;Net;P:pa\\:ss\\,word;;",
        )


if __name__ == "__main__":
    unittest.main()
