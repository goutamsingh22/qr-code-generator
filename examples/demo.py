"""Generate a few example QR codes."""

from pathlib import Path

from qrgen import Contact, QROptions, make_text, make_url, save_qr

OUTPUT = Path(__file__).parent / "output"


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    options = QROptions(error_correction="H", box_size=12, border=4)

    save_qr(make_text("Hello from qrgen!"), OUTPUT / "text.png", options)
    save_qr(make_url("https://example.com"), OUTPUT / "url.png", options)
    save_qr(
        Contact(
            name="Ada Lovelace",
            phone="+44 20 7946 0958",
            email="ada@example.com",
            organization="Analytical Engines",
            title="Mathematician",
            website="example.com",
        ).to_vcard(),
        OUTPUT / "contact.svg",
        options,
    )

    print(f"Wrote examples to {OUTPUT}")


if __name__ == "__main__":
    main()
