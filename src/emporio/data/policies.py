"""Page-level retrieval with source attribution from the supplied PDF."""
import re
from pathlib import Path
from pypdf import PdfReader
from emporio.data.catalog import normalize

TOPICS = {
    "store": ([2], "The store is at Rua 14 de Maio, 3200, Centro, Campo Grande. Monday to Friday 09:00–18:00, Saturday 09:00–13:00. Closed Sundays and holidays. Contact details conflict between sections, so I cannot confirm a single phone number."),
    "payments": ([3, 6], "PIX offers 5% off the list price with no stated minimum. Active promotions and PIX discounts do not stack. Card instalments depend on the amount and number of payments. External PIX financing is between you and your bank."),
    "returns": ([4, 7], "For online purchases, the manual allows a return request within 7 calendar days after receipt, subject to its conditions. I need the purchase channel, actual receipt date, item condition and reason before assessing a case. An estimated delivery date is not proof of receipt."),
    "delivery": ([4, 5], "The manual lists 1–3 business days for metropolitan Campo Grande. Outside that area, timing and cost depend on the carrier and destination. Local shipping is free above R$500 and R$35 below R$500. Exactly R$500 is not defined, so please confirm with the team."),
    "promotions": ([6, 7], "Only promotions marked active in the supplied data apply. Discounts never stack. We choose the highest applicable single discount and show the original price. Out-of-stock products are not available to purchase."),
    "warranty": ([7], "The manual describes 90 days of legal warranty for manufacturing defects from receipt. Manufacturer coverage varies. I cannot promise a product-specific manufacturer term without its warranty certificate."),
    "privacy": ([7, 8], "The manual limits personal data use to service, orders and stated purposes. Marketing requires explicit consent. This local prototype uses an order number and matching email as a demonstration check, not production authentication."),
}
ALIASES = {
    "hours": "store", "opening": "store", "address": "store", "horario": "store", "endereco": "store",
    "payment": "payments", "pix": "payments", "pagamento": "payments", "installment": "payments",
    "refund": "returns", "return": "returns", "devolucao": "returns", "troca": "returns",
    "shipping": "delivery", "frete": "delivery", "entrega": "delivery",
    "discount": "promotions", "desconto": "promotions", "garantia": "warranty",
}
class Policies:
    def __init__(self, path: Path):
        self.pages = [re.sub(r"\s+", " ", p.extract_text()).strip() for p in PdfReader(path).pages]
    def lookup(self, topic: str, question: str = ""):
        topic = normalize(topic)
        key = next((k for k in TOPICS if k == topic), None)
        if not key:
            key = next((value for word, value in ALIASES.items() if word in topic), None)
        if not key:
            return {"found": False, "topics": list(TOPICS), "message": "Choose a store policy topic."}
        pages, summary = TOPICS[key]
        from emporio.domain.policy_details import focused_policy
        focused = focused_policy(question)
        extra = {}
        if focused:
            pages, summary = focused.pop("pages"), focused.pop("summary")
            extra = focused
        return {"found": True, "topic": key, "summary": summary,
                **extra,
                "sources": [{"document": "políticas_da_loja.pdf", "page": n,
                             "text": self.pages[n-1]} for n in pages],
                "note": "Manual rules, not an independent legal assessment."}
