"""
QR code generation and cryptographic signing for offline ticket validation.

Each QR code payload is a JSON object signed with HMAC-SHA256:
{
  "ticket_id": "<uuid>",
  "user_id": "<uuid>",
  "agency_id": "<uuid>",
  "valid_until": "<ISO-8601>",
  "sig": "<hex>"
}

The validator device verifies the sig before accepting the ticket.
"""

import base64
import hashlib
import hmac
import io
import json
from datetime import datetime
from uuid import UUID

import qrcode
from qrcode.image.pure import PyPNGImage

from app.config import settings


def _build_payload(ticket_id: UUID, user_id: UUID, agency_id: UUID, valid_until: datetime) -> dict:
    return {
        "ticket_id": str(ticket_id),
        "user_id": str(user_id),
        "agency_id": str(agency_id),
        "valid_until": valid_until.isoformat(),
    }


def sign_ticket(ticket_id: UUID, user_id: UUID, agency_id: UUID, valid_until: datetime) -> str:
    """
    Create an HMAC-SHA256 signature over the ticket payload.

    Returns the hex-encoded signature string (stored in Ticket.signature).
    """
    payload = _build_payload(ticket_id, user_id, agency_id, valid_until)
    message = json.dumps(payload, sort_keys=True).encode()
    sig = hmac.new(settings.qr_secret_key.encode(), message, hashlib.sha256).hexdigest()
    return sig


def verify_signature(ticket_id: UUID, user_id: UUID, agency_id: UUID, valid_until: datetime, sig: str) -> bool:
    """Verify a ticket's HMAC signature."""
    expected = sign_ticket(ticket_id, user_id, agency_id, valid_until)
    return hmac.compare_digest(expected, sig)


def generate_qr_data(ticket_id: UUID, user_id: UUID, agency_id: UUID, valid_until: datetime, sig: str) -> str:
    """
    Build the QR code data string (JSON with embedded signature).

    This string is what gets encoded into the QR image.
    """
    payload = _build_payload(ticket_id, user_id, agency_id, valid_until)
    payload["sig"] = sig
    return json.dumps(payload, sort_keys=True)


def generate_qr_image_b64(qr_data: str) -> str:
    """
    Generate a QR code PNG image and return it as a base64 string.

    Suitable for embedding directly in an API response or HTML.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
