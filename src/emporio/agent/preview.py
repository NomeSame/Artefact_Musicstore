"""Explicitly limited, deterministic preview. This is not an LLM."""
import re
from emporio.data.catalog import normalize

def plan_preview(message, context):
    text = normalize(message)
    topics = {
        "returns": ["return", "refund", "devol", "troca"],
        "store": ["hours", "open", "address", "horario", "endereco"],
        "payments": ["payment", "installment", "pagamento", "parcel"],
        "delivery": ["shipping", "delivery", "frete", "entrega"],
        "warranty": ["warranty", "garantia"],
        "promotions": ["promotion", "discount", "promoc", "desconto"],
    }
    for topic, words in topics.items():
        if any(w in text for w in words):
            return "lookup_policy", {"topic": topic}
    if any(w in text for w in ["order", "pedido", "tracking"]):
        match = re.search(r"\b\d+\b", text)
        return ("get_order", {"order_id": int(match.group())}) if match else (None, {})
    if context.get("selected_product_id") and any(word in text for word in [
        "this instrument", "selected", "specification", "materials", "electronics",
        "sound-related", "build", "how many", "stock", "instrumento", "especificacoes", "materiais", "eletronica", "som", "estoque", "disponivel",
    ]):
        focus = ("sound" if any(w in text for w in ["sound-related", "electronics", "som", "eletronica"])
                 else "specifications" if any(w in text for w in ["specification", "materials", "build", "especificacoes", "materiais", "construcao"])
                 else "availability" if any(w in text for w in ["available", "stock", "how many", "disponivel", "estoque", "quantas"])
                 else "price" if any(w in text for w in ["cost", "price", "pix", "preco", "custa"]) else "overview")
        return "get_product", {"product_id": context["selected_product_id"], "focus": focus,
                               "payment": "pix" if "pix" in text else context.get("payment", "unspecified")}
    category = next((cid for word, cid in {
        "acoustic": 5, "violao": 5, "violoes": 5, "electric": 1, "guitarra": 1,
        "piano": 4, "keyboard": 4, "teclado": 4, "drum": 3, "bateria": 3,
        "bass": 2, "baixo": 2, "ukulele": 9, "violin": 8, "sax": 6, "trumpet": 7,
    }.items() if word in text), None)
    payment = "pix" if "pix" in text else context.get("payment", "unspecified")
    if context.get("selected_product_id") and not category and any(w in text for w in [
        "this", "selected", "that", "esse", "este", "price", "cost", "preco", "pix",
    ]):
        return "get_product", {"product_id": context["selected_product_id"], "payment": payment}
    limit = re.search(r"(?:under|below|up to|ate|r\$)\s*([\d.,]+)", text)
    if category or limit or any(w in text for w in ["find", "show", "available", "instrument", "catalog", "dispon"]):
        return "search_products", {
            "category_id": category or context.get("category_id"),
            "max_price": float(limit.group(1).replace(",", "")) if limit else context.get("max_price"),
            "payment": payment,
        }
    return None, {}
