import qrcode
from PIL import Image
from pathlib import Path

from django.template.loader import render_to_string
from django.conf import settings

from core.utils.brevo_email import send_email


# =========================
# EMAIL (Brevo API)
# =========================
def send_invoice_email(bill, pdf_path):
    """
    Send invoice email using Brevo API
    """

    subject = f"Invoice {bill.bill_number}"

    html_content = render_to_string(
        "billing/email_invoice.html",
        {"bill": bill}
    )

    send_email(
        subject=subject,
        html_content=html_content,
        to_email=bill.customer_email,
        attachments=[pdf_path],
    )


# =========================
# QR CODE GENERATION
# =========================
def generate_upi_qr(
    upi_uri: str,
    bill_number: str,
    logo_path: str = None,
    output_dir: str = None
):

    if output_dir is None:
        output_dir = Path(settings.MEDIA_ROOT) / "qr_codes"

    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    safe_name = bill_number.replace("/", "_")
    file_path = base_dir / f"{safe_name}.png"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGB")

    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path)
        qr_width, qr_height = qr_img.size
        logo_size = qr_width // 4
        logo = logo.resize((logo_size, logo_size))
        pos = (
            (qr_width - logo_size) // 2,
            (qr_height - logo_size) // 2
        )
        qr_img.paste(logo, pos)

    qr_img.save(file_path)

    return str(file_path)
