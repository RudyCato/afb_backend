"""
Barcode scanning support — powers the "Scan" button in Receiving / Returns and
generates SSCC-18 labels for pallets on close.

Two entry points:

    POST /scan/lookup                  raw barcode string in, decoded fields out
    POST /pallets/{id}/generate-sscc   assign a fresh SSCC-18 to a pallet

GS1-128 decoding is deliberately small: we only support the AIs a food
distributor actually needs — (00) SSCC, (01) GTIN, (10) batch/lot,
(17) expiration date. Unknown AIs are ignored gracefully so a scanner reading
a longer vendor label still returns partial data.

If no GS1 prefix is detected, we fall back to a plain product lookup by
Product.barcode — that handles UPC/EAN-13 case codes from suppliers.
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/scan", tags=["scan"])


# --------------------------------------------------------------------------- GS1-128 decoder
# Fixed-length AIs we care about. (Variable-length ones — like 10/lot — are
# terminated by ASCII group-separator 0x1D, or by end-of-string if they're
# last on the label.)
_FIXED_LEN = {
    "00": 18,   # SSCC
    "01": 14,   # GTIN
    "11": 6,    # production date  YYMMDD
    "13": 6,    # packaging date   YYMMDD
    "15": 6,    # best-before      YYMMDD
    "17": 6,    # expiration       YYMMDD
}
_VARIABLE_LEN_MAX = {
    "10": 20,   # batch / lot
    "21": 20,   # serial number
    "30": 8,    # count of items
}
_GS = "\x1d"   # ASCII group separator that terminates a variable-length AI


def _decode_yymmdd(s: str) -> date | None:
    if not (len(s) == 6 and s.isdigit()):
        return None
    yy, mm, dd = int(s[0:2]), int(s[2:4]), int(s[4:6])
    year = 2000 + yy if yy < 50 else 1900 + yy
    try:
        return date(year, mm, dd)
    except ValueError:
        return None


def decode_gs1_128(raw: str) -> dict:
    """Return a dict of parsed AI codes → values from a GS1-128 payload string.

    Accepts:
      - the raw payload with or without a leading FNC1 / "]C1" symbol
      - variable-length AIs terminated by \\x1d or end-of-string
      - non-GS1 payloads (returns empty dict; caller falls back to plain lookup)
    """
    s = raw.strip()
    # Strip the ]C1 symbology identifier some scanners emit.
    if s.startswith("]C1"):
        s = s[3:]
    # Fast-fail — if there are no known 2-digit AI codes, it's not GS1-128.
    if not re.match(r"^\d{2}", s):
        return {}

    out: dict = {}
    i = 0
    while i < len(s):
        ai = s[i : i + 2]
        i += 2
        if ai in _FIXED_LEN:
            length = _FIXED_LEN[ai]
            value = s[i : i + length]
            i += length
        elif ai in _VARIABLE_LEN_MAX:
            end = s.find(_GS, i)
            if end == -1:
                value = s[i : i + _VARIABLE_LEN_MAX[ai]]
                i = len(s)
            else:
                value = s[i:end]
                i = end + 1
        else:
            # Unknown AI — bail out with whatever we've parsed so far rather
            # than corrupt the rest of the string.
            break
        out[ai] = value
    return out


# --------------------------------------------------------------------------- SSCC generator
def _sscc_check_digit(seventeen: str) -> str:
    """GS1 Modulo-10 check digit — same algorithm as GTIN."""
    if not (seventeen.isdigit() and len(seventeen) == 17):
        raise ValueError("SSCC base must be exactly 17 digits.")
    total = 0
    for idx, ch in enumerate(reversed(seventeen)):
        total += int(ch) * (3 if idx % 2 == 0 else 1)
    return str((10 - (total % 10)) % 10)


def generate_sscc(*, serial_reference: int) -> str:
    """Build a full 18-digit SSCC.

    Uses env vars:
      SSCC_EXTENSION_DIGIT   1 char, 0-9   default "0"
      COMPANY_GS1_PREFIX     7-10 digits — your assigned GS1 Company Prefix
                             (or a placeholder for testing; production must
                             use a real prefix from GS1 US to be scannable
                             by trading partners)
    """
    ext = os.getenv("SSCC_EXTENSION_DIGIT", "0").strip() or "0"
    prefix = os.getenv("COMPANY_GS1_PREFIX", "0000000").strip() or "0000000"
    if not (ext.isdigit() and len(ext) == 1):
        raise ValueError("SSCC_EXTENSION_DIGIT must be a single digit 0-9.")
    if not (prefix.isdigit() and 7 <= len(prefix) <= 10):
        raise ValueError("COMPANY_GS1_PREFIX must be 7-10 digits.")
    serial_width = 17 - 1 - len(prefix)
    serial = str(serial_reference).zfill(serial_width)
    if len(serial) > serial_width:
        raise ValueError("Serial reference is too large for the configured GS1 prefix width.")
    base = ext + prefix + serial
    return base + _sscc_check_digit(base)


# --------------------------------------------------------------------------- schemas (kept
# local — small, endpoint-only shapes, no reason to bloat schemas.py)
class ScanLookupIn(BaseModel):
    raw: str


class ScanLookupOut(BaseModel):
    raw: str
    decoded_ais: dict = {}     # every GS1 AI we recognized
    product_id: int | None = None
    sku: str | None = None
    product_name: str | None = None
    lot_code: str | None = None
    sell_by_date: date | None = None
    sscc: str | None = None
    matched_by: str            # "gtin" | "sscc" | "barcode" | "none"
    note: str | None = None


# --------------------------------------------------------------------------- routes
@router.post("/lookup", response_model=ScanLookupOut)
def scan_lookup(payload: ScanLookupIn, db: Session = Depends(get_db)):
    """Decode a scanned barcode and return everything we know about it.

    Called from the Receiving and Returns UI: staff clicks Scan, points the
    camera / hits the trigger, this endpoint decodes and the form fills.
    """
    raw = (payload.raw or "").strip()
    if not raw:
        raise HTTPException(422, "Empty scan payload.")

    ais = decode_gs1_128(raw)

    out = ScanLookupOut(raw=raw, decoded_ais=ais, matched_by="none")

    # GS1-128 case label
    if ais:
        if "10" in ais:
            out.lot_code = ais["10"]
        # Prefer expiration (17), fall back to best-before (15).
        for date_ai in ("17", "15", "11"):
            if date_ai in ais:
                out.sell_by_date = _decode_yymmdd(ais[date_ai])
                if out.sell_by_date:
                    break
        if "00" in ais:
            out.sscc = ais["00"]
            out.matched_by = "sscc"
        if "01" in ais:
            gtin14 = ais["01"]
            # Try to match Product.barcode against the last 12 (UPC-A),
            # last 13 (EAN-13), or the full 14 digits — vendors ship any of them.
            prod = (
                db.query(models.Product)
                .filter(models.Product.barcode.in_([gtin14, gtin14[-13:], gtin14[-12:]]))
                .first()
            )
            if prod:
                out.product_id = prod.id
                out.sku = prod.sku
                out.product_name = prod.name
                out.matched_by = "gtin"
            else:
                out.note = f"GTIN {gtin14} scanned but no matching Product.barcode in the catalog yet."
        return out

    # Plain UPC / internal barcode — no GS1 prefix at all.
    prod = db.query(models.Product).filter(models.Product.barcode == raw).first()
    if prod:
        out.product_id = prod.id
        out.sku = prod.sku
        out.product_name = prod.name
        out.matched_by = "barcode"
    else:
        out.note = "No GS1-128 data recognized and no product matches this barcode. Save the product and set its Barcode field, then try again."
    return out


class PalletSsccOut(BaseModel):
    id: int
    pallet_number: str
    sscc: str


@router.post("/pallets/{pallet_id}/generate-sscc", response_model=PalletSsccOut, tags=["pallets"])
def assign_pallet_sscc(pallet_id: int, db: Session = Depends(get_db)):
    """Generate + persist an SSCC-18 on this pallet. Idempotent — returns the
    existing SSCC if one has already been assigned, so calling twice is safe."""
    pallet = db.query(models.Pallet).get(pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found.")
    if pallet.sscc:
        return PalletSsccOut(id=pallet.id, pallet_number=pallet.pallet_number, sscc=pallet.sscc)
    try:
        sscc = generate_sscc(serial_reference=pallet.id)
    except ValueError as e:
        raise HTTPException(500, f"SSCC generation misconfigured: {e}")
    # Uniqueness guard — retry once with a bumped serial if we somehow collide
    # (only possible if COMPANY_GS1_PREFIX changed between deploys).
    if db.query(models.Pallet).filter(models.Pallet.sscc == sscc).first():
        sscc = generate_sscc(serial_reference=pallet.id + 1_000_000)
    pallet.sscc = sscc
    db.commit()
    db.refresh(pallet)
    return PalletSsccOut(id=pallet.id, pallet_number=pallet.pallet_number, sscc=pallet.sscc)
