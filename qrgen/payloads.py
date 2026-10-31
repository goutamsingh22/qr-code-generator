"""Build the text that goes inside a QR code.

QR codes are just containers for text.  Scanners decide what to do with the
content based on its format, so this module knows how to produce the common
payloads:

* plain text
* web URLs
* vCard contact cards
* ``mailto:`` e-mail links
* ``SMSTO:`` text messages
* ``WIFI:`` network join codes
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlparse

__all__ = [
    "Contact",
    "PayloadError",
    "make_contact",
    "make_email",
    "make_sms",
    "make_text",
    "make_url",
    "make_wifi",
]


class PayloadError(ValueError):
    """Raised when a payload cannot be built from the supplied values."""


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _require(value: str | None, field: str) -> str:
    """Return ``value`` stripped, or raise when it is empty."""
    if value is None or not value.strip():
        raise PayloadError(f"{field} must not be empty")
    return value.strip()


def _normalize_url(url: str) -> str:
    """Add ``https://`` when missing and check that the URL makes sense."""
    value = _require(url, "URL")
    if any(character.isspace() for character in value):
        raise PayloadError(f"invalid URL: {url!r}")

    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
        parsed = urlparse(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise PayloadError(f"unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.netloc:
        raise PayloadError(f"invalid URL: {url!r}")
    return value


def _escape_vcard(value: str) -> str:
    """Escape the characters that have a meaning inside a vCard line."""
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _escape_wifi(value: str) -> str:
    """Escape the characters that have a meaning inside a WIFI payload."""
    for character in ("\\", ";", ",", ":", '"'):
        value = value.replace(character, f"\\{character}")
    return value


# --------------------------------------------------------------------------- #
# payloads
# --------------------------------------------------------------------------- #
def make_text(text: str) -> str:
    """Return ``text`` unchanged, ready to be encoded."""
    if not text or not text.strip():
        raise PayloadError("text must not be empty")
    return text


def make_url(url: str) -> str:
    """Return a valid http(s) URL, adding ``https://`` when needed."""
    return _normalize_url(url)


@dataclass
class Contact:
    """A contact card that can be rendered as a vCard 3.0 payload."""

    name: str
    phone: str | None = None
    email: str | None = None
    organization: str | None = None
    title: str | None = None
    address: str | None = None
    website: str | None = None
    note: str | None = None

    def to_vcard(self) -> str:
        """Return the contact as a vCard 3.0 string."""
        name = _require(self.name, "contact name")

        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{_escape_vcard(name)};;;;",
            f"FN:{_escape_vcard(name)}",
        ]

        if self.organization:
            lines.append(f"ORG:{_escape_vcard(self.organization)}")
        if self.title:
            lines.append(f"TITLE:{_escape_vcard(self.title)}")
        if self.phone:
            lines.append(f"TEL;TYPE=CELL:{_escape_vcard(self.phone)}")
        if self.email:
            lines.append(f"EMAIL;TYPE=INTERNET:{_escape_vcard(self.email)}")
        if self.address:
            lines.append(f"ADR;TYPE=WORK:;;{_escape_vcard(self.address)};;;;")
        if self.website:
            lines.append(f"URL:{_escape_vcard(_normalize_url(self.website))}")
        if self.note:
            lines.append(f"NOTE:{_escape_vcard(self.note)}")

        lines.append("END:VCARD")
        return "\r\n".join(lines) + "\r\n"


def make_contact(
    name: str,
    phone: str | None = None,
    email: str | None = None,
    organization: str | None = None,
    title: str | None = None,
    address: str | None = None,
    website: str | None = None,
    note: str | None = None,
) -> str:
    """Build a vCard payload for a contact."""
    return Contact(
        name=name,
        phone=phone,
        email=email,
        organization=organization,
        title=title,
        address=address,
        website=website,
        note=note,
    ).to_vcard()


def make_email(email: str, subject: str | None = None, body: str | None = None) -> str:
    """Build a ``mailto:`` payload, optionally with subject and body."""
    address = _require(email, "e-mail address")
    if "@" not in address or any(character.isspace() for character in address):
        raise PayloadError(f"invalid e-mail address: {email!r}")

    payload = f"mailto:{address}"
    parameters = []
    if subject:
        parameters.append(f"subject={quote(subject, safe='')}")
    if body:
        parameters.append(f"body={quote(body, safe='')}")
    if parameters:
        payload += "?" + "&".join(parameters)
    return payload


def make_sms(phone: str, message: str | None = None) -> str:
    """Build an ``SMSTO:`` payload for a text message."""
    number = _require(phone, "phone number")
    payload = f"SMSTO:{number}"
    if message:
        payload += f":{message}"
    return payload


def make_wifi(
    ssid: str,
    password: str | None = None,
    security: str = "WPA",
    hidden: bool = False,
) -> str:
    """Build a ``WIFI:`` payload that joins a wireless network."""
    network = _escape_wifi(_require(ssid, "network name"))
    security = security.upper()

    if security not in {"WPA", "WEP", "NOPASS"}:
        raise PayloadError(f"unsupported Wi-Fi security: {security!r}")
    if security == "NOPASS":
        if password:
            raise PayloadError("an open network cannot have a password")
        secret = ""
    else:
        secret = _escape_wifi(_require(password, "Wi-Fi password"))

    payload = f"WIFI:T:{security};S:{network};P:{secret};"
    if hidden:
        payload += "H:true;"
    return payload + ";"
