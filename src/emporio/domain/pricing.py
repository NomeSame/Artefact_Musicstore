"""Exact money calculations, independent of the UI and model."""
from decimal import Decimal, ROUND_HALF_UP

def cents(value: str | int | Decimal) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def quote(list_cents: int, promotion_percent: int = 0, payment: str = "unspecified") -> dict:
    if payment not in {"unspecified", "pix", "card", "debit", "boleto"}:
        raise ValueError("Unknown payment method.")
    if list_cents < 0 or not 0 <= promotion_percent <= 100:
        raise ValueError("Invalid price or discount.")
    discount = max(promotion_percent, 5 if payment == "pix" else 0)
    amount = int((Decimal(list_cents) * (100 - discount) / 100).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP))
    return {
        "list_cents": list_cents, "price_cents": amount,
        "discount_percent": discount, "payment": payment,
        "discount_source": "promotion" if discount and discount == promotion_percent else "pix" if discount else None,
        "pix_price_cents": quote(list_cents, promotion_percent, "pix")["price_cents"] if payment != "pix" else amount,
    }
