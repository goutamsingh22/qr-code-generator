"""Tests for the command line interface."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from qrgen.cli import build_parser, main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def run_cli(self, *arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_parser_has_all_commands(self):
        parser = build_parser()
        actions = [
            action
            for action in parser._actions
            if action.dest == "command"
        ]
        self.assertEqual(len(actions), 1)
        self.assertEqual(
            set(actions[0].choices),
            {"text", "url", "contact", "email", "sms", "wifi"},
        )

    def test_text_command(self):
        output = self.path / "text.png"
        code, _, stderr = self.run_cli("text", "Hello, world!", "-o", str(output))
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())
        self.assertIn("Saved QR code", stderr)

    def test_url_command(self):
        output = self.path / "url.svg"
        code, _, _ = self.run_cli("url", "example.com", "-o", str(output))
        self.assertEqual(code, 0)
        self.assertIn("<svg", output.read_text(encoding="utf-8"))

    def test_contact_command(self):
        output = self.path / "contact.png"
        code, _, _ = self.run_cli(
            "contact",
            "--name",
            "Ada Lovelace",
            "--phone",
            "+44 20 7946 0958",
            "--email",
            "ada@example.com",
            "-o",
            str(output),
        )
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())

    def test_email_command(self):
        output = self.path / "email.png"
        code, _, _ = self.run_cli(
            "email",
            "ada@example.com",
            "--subject",
            "Hello",
            "-o",
            str(output),
        )
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())

    def test_sms_command(self):
        output = self.path / "sms.png"
        code, _, _ = self.run_cli("sms", "+15551234567", "--message", "Hi", "-o", str(output))
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())

    def test_wifi_command(self):
        output = self.path / "wifi.png"
        code, _, _ = self.run_cli(
            "wifi",
            "MyNetwork",
            "--password",
            "secret",
            "-o",
            str(output),
        )
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())

    def test_terminal_output(self):
        output = self.path / "terminal.png"
        code, stdout, _ = self.run_cli("text", "hello", "--terminal", "-o", str(output))
        self.assertEqual(code, 0)
        self.assertIn("\u2588\u2588", stdout)
        self.assertTrue(output.exists())

    def test_terminal_only_does_not_save(self):
        code, stdout, _ = self.run_cli("text", "hello", "--terminal")
        self.assertEqual(code, 0)
        self.assertIn("\u2588\u2588", stdout)

    def test_invalid_url_returns_error(self):
        code, _, stderr = self.run_cli("url", "ftp://example.com", "-o", "unused.png")
        self.assertEqual(code, 2)
        self.assertIn("error:", stderr)

    def test_missing_contact_name_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["contact", "--phone", "123"])

    def test_no_command_prints_help(self):
        code, stdout, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("usage:", stdout)

    def test_version(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("qrgen", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
