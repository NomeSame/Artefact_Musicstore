"""Factual product descriptions derived only from supplied catalogue fields."""
LABELS = {
    "top": "Top", "back_sides": "Back and sides", "neck": "Neck", "strings": "Strings",
    "scale": "Scale length", "electronics": "Electronics", "color": "Colour",
    "body": "Body", "pickups": "Pickups", "pickup": "Pickup", "frets": "Frets",
    "keys": "Keys", "type": "Type", "polyphony": "Polyphony", "size": "Size",
    "fingerboard": "Fingerboard", "bridge": "Bridge", "finish": "Finish",
}
SOUND_FIELDS = {"electronics", "pickups", "pickup", "strings", "type", "top",
                "back_sides", "body", "keys", "polyphony", "tuning"}
def specification_lines(product, sound_only=False):
    pairs = [(key, value) for key, value in product["specs"].items()
             if not sound_only or key in SOUND_FIELDS]
    return [f"{LABELS.get(key, key.replace('_', ' ').capitalize())}: {value}" for key, value in pairs]

def product_information(product, focus):
    name = product["name"]
    if focus == "availability":
        if product["available"]:
            count = product["stock_quantity"]
            return f"{name} has {count} {'unit' if count == 1 else 'units'} available in the supplied stock data."
        status = "out of stock" if product["status"] == "active" else product["status"].replace("_", " ")
        return f"{name} is currently listed as {status}. I cannot confirm a purchase or replenishment date."
    lines = specification_lines(product, sound_only=focus == "sound")
    if focus == "sound":
        details = "\n".join(lines) if lines else "No sound-related specifications are recorded for this instrument."
        return (f"Here are the recorded sound and setup details for {name}.\n{details}\n\n"
                "Specifications cannot confirm its tone or playing feel. Please, ask the team about a listening demo or trying it in person.")
    if focus == "specifications":
        details = "\n".join(specification_lines(product)) or "No technical specifications are recorded."
        return f"Here are the recorded specifications for {name}.\n{details}"
    return (f"{name}\n\n{product['description']}\n\n" +
            ("Recorded details\n" + "\n".join(lines) if lines else "Ask the team for model-specific specifications."))
