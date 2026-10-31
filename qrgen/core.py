"""Create, render and save QR codes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from qrcode.exceptions import DataOverflowError
from qrcode.image.svg import SvgPathImage

__all__ = [
    "QRError",
    "QROptions",
    "build_qr",
    "render_ascii",
    "save_qr",
]

ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
SUPPORTED_EXTENSIONS = RASTER_EXTENSIONS | {".svg"}


class QRError(Exception):
    """Raised when a QR code cannot be built or saved."""


@dataclass(frozen=True)
class QROptions:
    """Settings that control how a QR code is generated."""

    error_correction: str = "M"
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    back_color: str = "white"
    version: int | None = None

    def __post_init__(self) -> None:
        if self.error_correction.upper() not in ERROR_CORRECTION_LEVELS:
            raise QRError(
                f"error correction must be one of {', '.join(ERROR_CORRECTION_LEVELS)}"
            )
        if not 1 <= self.box_size <= 100:
            raise QRError("box size must be between 1 and 100")
        if self.border < 0:
            raise QRError("border must be zero or greater")
        if self.version is not None and not 1 <= self.version <= 40:
            raise QRError("QR version must be between 1 and 40")


def build_qr(data: str, options: QROptions | None = None) -> qrcode.QRCode:
    """Return a :class:`qrcode.QRCode` for ``data``."""
    options = options or QROptions()
    if not isinstance(data, str) or not data:
        raise QRError("QR data must be a non-empty string")

    qr = qrcode.QRCode(
        version=options.version,
        error_correction=ERROR_CORRECTION_LEVELS[options.error_correction.upper()],
        box_size=options.box_size,
        border=options.border,
    )
    try:
        qr.add_data(data)
        qr.make(fit=options.version is None)
    except (DataOverflowError, ValueError) as error:
        raise QRError(f"could not encode data: {error}") from error
    return qr


def save_qr(
    data: str,
    output: str | Path,
    options: QROptions | None = None,
) -> Path:
    """Save a QR code for ``data`` and return the written path.

    The image format is taken from the file extension.  ``.svg`` produces a
    vector image, every other supported extension produces a raster image
    through Pillow.  A missing extension defaults to ``.png``.
    """
    options = options or QROptions()
    path = Path(output)

    if path.exists() and path.is_dir():
        raise QRError(f"output path is a directory: {path}")

    suffix = path.suffix.lower()
    if not suffix:
        path = path.with_suffix(".png")
        suffix = ".png"
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise QRError(f"unsupported image format {suffix!r} (use one of: {supported})")

    qr = build_qr(data, options)
    try:
        if suffix == ".svg":
            image = qr.make_image(
                image_factory=SvgPathImage,
                fill_color=options.fill_color,
                back_color=options.back_color,
            )
        else:
            image = qr.make_image(
                fill_color=options.fill_color,
                back_color=options.back_color,
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path))
    except (OSError, ValueError) as error:
        raise QRError(f"could not save QR code: {error}") from error
    return path


def render_ascii(
    data: str,
    options: QROptions | None = None,
    invert: bool = False,
    ascii_only: bool = False,
) -> str:
    """Render a QR code as text using two-character blocks.

    ``ascii_only`` replaces the Unicode block glyphs with ``##`` so the result
    can be printed on terminals that cannot encode box-drawing characters.
    """
    qr = build_qr(data, options)
    black, white = ("##", "  ") if ascii_only else ("\u2588\u2588", "  ")
    if invert:
        black, white = white, black
    return "\n".join(
        "".join(black if module else white for module in row) for row in qr.get_matrix()
    )
