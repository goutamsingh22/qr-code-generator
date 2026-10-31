"""Generate QR codes for text, URLs, contacts and more."""

from .core import QRError, QROptions, build_qr, render_ascii, save_qr
from .payloads import (
    Contact,
    PayloadError,
    make_contact,
    make_email,
    make_sms,
    make_text,
    make_url,
    make_wifi,
)

__version__ = "1.0.0"

__all__ = [
    "Contact",
    "PayloadError",
    "QRError",
    "QROptions",
    "build_qr",
    "make_contact",
    "make_email",
    "make_sms",
    "make_text",
    "make_url",
    "make_wifi",
    "render_ascii",
    "save_qr",
    "__version__",
]
