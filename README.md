# qrgen - Python QR Code Generator

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-54%20passing-brightgreen.svg)](tests)
[![Powered by qrcode](https://img.shields.io/badge/powered%20by-qrcode-informational.svg)](https://github.com/lincolnloop/python-qrcode)

A small command line tool and Python library for generating QR codes from plain
text, web URLs, vCard contact details, e-mail links, SMS messages and Wi-Fi
join codes. Images can be saved as PNG, SVG, JPG, BMP, GIF or WebP, or printed
straight to the terminal.

---

## Features

| Feature | Description |
| --- | --- |
| Plain text | Encode any text, including notes and identifiers |
| URLs | Adds `https://` when the scheme is missing and validates the result |
| Contact cards | vCard 3.0 with name, phone, e-mail, organisation, title, address, website and note |
| E-mail links | `mailto:` payloads with pre-filled subject and body |
| SMS links | `SMSTO:` payloads with a pre-filled message |
| Wi-Fi codes | WPA, WEP and open networks, including hidden networks |
| PNG and SVG | Raster output through Pillow, vector output through qrcode's SVG factory |
| Terminal preview | Print a scannable QR code with `--terminal` |
| Customisation | Error correction level, module size, quiet zone, foreground and background colours, forced version |
| Python API | Build payloads and save images from your own code |
| Tests | Unit tests for payloads, rendering and the CLI |

---

## Installation

```bash
# from a clone
git clone https://github.com/goutamsingh22/qr-code-generator.git
cd qr-code-generator
pip install .

# development install with the test tools
pip install -e ".[dev]"
```

The only runtime dependency is [`qrcode`](https://pypi.org/project/qrcode/)
with its Pillow extra for raster images. You can also run it straight from the
source tree:

```bash
python -m qrgen text "Hello, world!"
```

---

## Quick start

```bash
# plain text
qrgen text "Hello, world!" -o hello.png

# a URL, with https:// added automatically
qrgen url example.com -o example.svg

# a contact card
qrgen contact --name "Ada Lovelace" \
  --phone "+44 20 7946 0958" \
  --email "ada@example.com" \
  --organization "Analytical Engines" \
  --title "Mathematician" \
  --website "example.com" \
  -o ada.png

# preview a QR code in the terminal
qrgen wifi "MyNetwork" --password "secret" --terminal
```

---

## Commands

### `text` - plain text

```bash
qrgen text [options] TEXT
```

```bash
qrgen text "Meeting at 10:00 in room 4" -o meeting.png
```

### `url` - web URL

```bash
qrgen url [options] URL
```

```bash
qrgen url example.com/path -o link.png
```

A missing scheme becomes `https://`. Only `http` and `https` URLs are accepted,
and whitespace inside the URL is rejected.

### `contact` - vCard contact details

```bash
qrgen contact [options] --name NAME
```

| Option | Description |
| --- | --- |
| `--name` | Full name (required) |
| `--phone` | Phone number |
| `--email` | E-mail address |
| `--organization` | Company or organisation |
| `--title` | Job title |
| `--address` | Postal address |
| `--website` | Website URL |
| `--note` | Free-form note |

```bash
qrgen contact --name "Grace Hopper" --phone "+1 555 0100" --email grace@example.com
```

The payload is a vCard 3.0 card, so phone cameras and contact apps can import
it directly.

### `email` - mailto link

```bash
qrgen email [options] EMAIL
```

```bash
qrgen email ada@example.com --subject "Hello" --body "Nice to meet you"
```

### `sms` - pre-filled text message

```bash
qrgen sms [options] PHONE
```

```bash
qrgen sms "+15551234567" --message "On my way!"
```

### `wifi` - network join code

```bash
qrgen wifi [options] SSID
```

| Option | Description | Default |
| --- | --- | --- |
| `--password` | Network password | - |
| `--security` | `WPA`, `WEP` or `nopass` | `WPA` |
| `--hidden` | Mark the network as hidden | off |

```bash
qrgen wifi "Cafe Guest" --security nopass
```

---

## Output options

Every command accepts the same image options:

| Option | Description | Default |
| --- | --- | --- |
| `-o, --output` | Output file; format comes from the extension | `qr-<command>.png` |
| `--terminal` | Also print the QR code to the terminal | off |
| `-e, --error-correction` | `L`, `M`, `Q` or `H` | `M` |
| `--box-size` | Pixels per QR module | `10` |
| `--border` | Quiet zone width in modules | `4` |
| `--fill` | Foreground colour (name or hex) | `black` |
| `--back` | Background colour (name or hex) | `white` |
| `--qr-version` | Force a version from 1 to 40 | auto |

Supported extensions: `.png`, `.svg`, `.jpg`, `.jpeg`, `.bmp`, `.gif` and
`.webp`. A file without an extension gets `.png`.

```bash
qrgen url example.com -o dark.svg --fill "#003366" --back "#ffffff" -e H
```

Higher error correction (`Q` or `H`) makes a QR code more robust when it is
printed small, dirty or partially covered, at the cost of a denser code.

On terminals that cannot display Unicode block characters, `--terminal`
automatically falls back to an ASCII preview made of `##` blocks.

---

## Python API

```python
from qrgen import (
    Contact,
    QROptions,
    make_contact,
    make_email,
    make_sms,
    make_text,
    make_url,
    make_wifi,
    render_ascii,
    save_qr,
)

# payload builders return the text that goes inside the QR code
text = make_text("Hello, world!")
url = make_url("example.com")                       # https://example.com
email = make_email("ada@example.com", subject="Hi")
sms = make_sms("+15551234567", "On my way!")
wifi = make_wifi("MyNetwork", "secret")
card = make_contact(name="Ada Lovelace", phone="+44 20 7946 0958")

# or use the Contact object directly
card = Contact(name="Ada Lovelace", email="ada@example.com").to_vcard()

# save as PNG, SVG or any other supported format
options = QROptions(error_correction="H", box_size=12, fill_color="#003366")
save_qr(card, "ada.png", options)
save_qr(url, "example.svg", options)

# preview in a terminal
print(render_ascii(text, options))
```

### `QROptions`

| Field | Default | Meaning |
| --- | --- | --- |
| `error_correction` | `"M"` | `L` (7%), `M` (15%), `Q` (25%) or `H` (30%) recovery |
| `box_size` | `10` | Pixels per module |
| `border` | `4` | Quiet zone width in modules |
| `fill_color` | `"black"` | Foreground colour |
| `back_color` | `"white"` | Background colour |
| `version` | `None` | Force a QR version (1-40); `None` fits automatically |

---

## Project structure

```text
qr-code-generator/
├── qrgen/
│   ├── __init__.py       # public API
│   ├── __main__.py       # python -m qrgen
│   ├── cli.py            # argparse based command line interface
│   ├── core.py           # QR creation, saving and terminal rendering
│   └── payloads.py       # text, URL, vCard, e-mail, SMS and Wi-Fi payloads
├── tests/
│   ├── test_cli.py
│   ├── test_core.py
│   └── test_payloads.py
├── examples/
│   └── demo.py
├── .github/workflows/ci.yml
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Examples

```bash
python -m examples.demo
```

This writes `text.png`, `url.png` and `contact.svg` to `examples/output/`.

---

## Testing

```bash
python -m pytest -q
# or
python -m unittest discover -s tests -v
```

Lint with:

```bash
ruff check .
```

---

## Notes

- QR codes are not encrypted. Anyone who scans the code can read its contents.
- Wi-Fi QR codes contain the network password in plain text. Print or share
  them carefully.
- vCard escaping follows the vCard 3.0 rules for backslashes, semicolons,
  commas and newlines.
- URLs are normalised to `http` or `https`; other schemes such as `ftp` and
  `javascript` are rejected.

---
