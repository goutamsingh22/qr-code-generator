"""Tests for QR creation and rendering."""

import tempfile
import unittest
from pathlib import Path

from qrgen.core import QRError, QROptions, build_qr, render_ascii, save_qr


class BuildQRTests(unittest.TestCase):
    def test_builds_a_matrix(self):
        qr = build_qr("hello")
        matrix = qr.get_matrix()
        self.assertGreater(len(matrix), 0)
        self.assertTrue(all(isinstance(cell, bool) for row in matrix for cell in row))

    def test_rejects_empty_data(self):
        with self.assertRaises(QRError):
            build_qr("")

    def test_forced_version(self):
        qr = build_qr("hello", QROptions(version=5))
        self.assertEqual(qr.version, 5)

    def test_rejects_invalid_error_correction(self):
        with self.assertRaises(QRError):
            QROptions(error_correction="X")

    def test_rejects_invalid_box_size(self):
        with self.assertRaises(QRError):
            QROptions(box_size=0)

    def test_rejects_invalid_border(self):
        with self.assertRaises(QRError):
            QROptions(border=-1)

    def test_rejects_invalid_version(self):
        with self.assertRaises(QRError):
            QROptions(version=41)


class SaveQRTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_saves_png(self):
        output = save_qr("hello", self.path / "hello.png")
        self.assertTrue(output.exists())
        self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_saves_svg(self):
        output = save_qr("hello", self.path / "hello.svg")
        self.assertTrue(output.exists())
        self.assertIn("<svg", output.read_text(encoding="utf-8"))

    def test_adds_png_extension(self):
        output = save_qr("hello", self.path / "hello")
        self.assertEqual(output.suffix, ".png")
        self.assertTrue(output.exists())

    def test_creates_parent_directories(self):
        output = save_qr("hello", self.path / "nested" / "hello.png")
        self.assertTrue(output.exists())

    def test_rejects_unsupported_extension(self):
        with self.assertRaises(QRError):
            save_qr("hello", self.path / "hello.txt")

    def test_rejects_directory_output(self):
        with self.assertRaises(QRError):
            save_qr("hello", self.path)

    def test_custom_colours(self):
        output = save_qr(
            "hello",
            self.path / "coloured.png",
            QROptions(fill_color="#003366", back_color="#ffffff"),
        )
        self.assertTrue(output.exists())


class AsciiTests(unittest.TestCase):
    def test_renders_blocks(self):
        rendered = render_ascii("hello")
        self.assertIn("\u2588\u2588", rendered)
        self.assertGreater(len(rendered.splitlines()), 1)

    def test_inverted(self):
        normal = render_ascii("hello")
        inverted = render_ascii("hello", invert=True)
        self.assertNotEqual(normal, inverted)

    def test_ascii_only(self):
        rendered = render_ascii("hello", ascii_only=True)
        self.assertIn("##", rendered)
        self.assertNotIn("\u2588", rendered)


if __name__ == "__main__":
    unittest.main()
