"""QR code generation utilities."""
import base64
import io

import qrcode
from qrcode.image.pure import PyPNGImage


def generate_qr_base64(url: str) -> str:
    """Generate a QR code PNG for the given URL and return as base64 string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")
