"""Command line interface for the QR code generator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .core import QRError, QROptions, render_ascii, save_qr
from .payloads import (
    PayloadError,
    make_contact,
    make_email,
    make_sms,
    make_text,
    make_url,
    make_wifi,
)

__all__ = ["build_parser", "main"]

DEFAULT_OUTPUTS = {
    "text": "qr-text.png",
    "url": "qr-url.png",
    "contact": "qr-contact.png",
    "email": "qr-email.png",
    "sms": "qr-sms.png",
    "wifi": "qr-wifi.png",
}


def _options_from_args(args: argparse.Namespace) -> QROptions:
    return QROptions(
        error_correction=args.error_correction,
        box_size=args.box_size,
        border=args.border,
        fill_color=args.fill,
        back_color=args.back,
        version=args.qr_version,
    )


def _can_encode(text: str) -> bool:
    """Return whether the current standard output can encode ``text``."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def _print_terminal(data: str, options: QROptions) -> None:
    """Print a QR code, falling back to ASCII on limited terminals."""
    print(render_ascii(data, options, ascii_only=not _can_encode("\u2588\u2588")))


def _emit(data: str, args: argparse.Namespace, command: str) -> int:
    """Save and/or print a QR code for ``data``."""
    options = _options_from_args(args)
    output = args.output

    if output is None and not args.terminal:
        output = DEFAULT_OUTPUTS[command]

    if output is not None:
        path = save_qr(data, output, options)
        print(f"Saved QR code to {path}", file=sys.stderr)

    if args.terminal:
        _print_terminal(data, options)

    return 0


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_text(args: argparse.Namespace) -> int:
    return _emit(make_text(args.text), args, "text")


def cmd_url(args: argparse.Namespace) -> int:
    return _emit(make_url(args.url), args, "url")


def cmd_contact(args: argparse.Namespace) -> int:
    data = make_contact(
        name=args.name,
        phone=args.phone,
        email=args.email,
        organization=args.organization,
        title=args.title,
        address=args.address,
        website=args.website,
        note=args.note,
    )
    return _emit(data, args, "contact")


def cmd_email(args: argparse.Namespace) -> int:
    return _emit(make_email(args.email, subject=args.subject, body=args.body), args, "email")


def cmd_sms(args: argparse.Namespace) -> int:
    return _emit(make_sms(args.phone, message=args.message), args, "sms")


def cmd_wifi(args: argparse.Namespace) -> int:
    data = make_wifi(
        args.ssid,
        password=args.password,
        security=args.security,
        hidden=args.hidden,
    )
    return _emit(data, args, "wifi")


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #
def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o",
        "--output",
        help="output image (PNG, SVG, JPG, ...); defaults to a name based on the command",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="print the QR code to the terminal (in addition to saving a file)",
    )
    parser.add_argument(
        "-e",
        "--error-correction",
        choices=("L", "M", "Q", "H"),
        default="M",
        help="error correction level (default: M)",
    )
    parser.add_argument(
        "--box-size",
        type=int,
        default=10,
        metavar="PIXELS",
        help="pixels per QR module (default: 10)",
    )
    parser.add_argument(
        "--border",
        type=int,
        default=4,
        metavar="MODULES",
        help="quiet zone width in modules (default: 4)",
    )
    parser.add_argument("--fill", default="black", help="foreground colour (default: black)")
    parser.add_argument("--back", default="white", help="background colour (default: white)")
    parser.add_argument(
        "--qr-version",
        type=int,
        default=None,
        metavar="1-40",
        help="force a QR version instead of fitting the data automatically",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``qrgen`` command."""
    parser = argparse.ArgumentParser(
        prog="qrgen",
        description="Generate QR codes for text, URLs, contacts, e-mail, SMS and Wi-Fi.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  qrgen text 'Hello, world!' -o hello.png\n"
            "  qrgen url example.com -o example.png\n"
            "  qrgen contact --name 'Ada Lovelace' --phone '+44 20 7946 0958' \\\n"
            "      --email ada@example.com -o ada.png\n"
            "  qrgen wifi 'MyNetwork' --password 'secret' --terminal\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    text = subparsers.add_parser("text", help="encode plain text")
    text.add_argument("text", help="the text to encode")
    _add_output_options(text)
    text.set_defaults(func=cmd_text)

    url = subparsers.add_parser("url", help="encode a web URL")
    url.add_argument("url", help="the URL to encode (https:// is added when missing)")
    _add_output_options(url)
    url.set_defaults(func=cmd_url)

    contact = subparsers.add_parser("contact", help="encode contact details as a vCard")
    contact.add_argument("--name", required=True, help="full name")
    contact.add_argument("--phone", help="phone number")
    contact.add_argument("--email", help="e-mail address")
    contact.add_argument("--organization", help="company or organisation")
    contact.add_argument("--title", help="job title")
    contact.add_argument("--address", help="postal address")
    contact.add_argument("--website", help="website URL")
    contact.add_argument("--note", help="free-form note")
    _add_output_options(contact)
    contact.set_defaults(func=cmd_contact)

    email = subparsers.add_parser("email", help="encode a mailto: link")
    email.add_argument("email", help="recipient e-mail address")
    email.add_argument("--subject", help="pre-filled subject")
    email.add_argument("--body", help="pre-filled message body")
    _add_output_options(email)
    email.set_defaults(func=cmd_email)

    sms = subparsers.add_parser("sms", help="encode a pre-filled text message")
    sms.add_argument("phone", help="recipient phone number")
    sms.add_argument("--message", help="pre-filled message")
    _add_output_options(sms)
    sms.set_defaults(func=cmd_sms)

    wifi = subparsers.add_parser("wifi", help="encode a Wi-Fi network join code")
    wifi.add_argument("ssid", help="network name")
    wifi.add_argument("--password", help="network password")
    wifi.add_argument(
        "--security",
        choices=("WPA", "WEP", "nopass"),
        default="WPA",
        help="network security type (default: WPA)",
    )
    wifi.add_argument("--hidden", action="store_true", help="mark the network as hidden")
    _add_output_options(wifi)
    wifi.set_defaults(func=cmd_wifi)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``qrgen`` command."""
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return int(args.func(args) or 0)
    except (PayloadError, QRError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # pragma: no cover
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
