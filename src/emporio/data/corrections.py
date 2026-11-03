"""Explicit, owner-approved corrections to the derived catalogue, not its sources."""
import json

# Marco chose this reassignment after reviewing the conflicting source entries.
# The descriptive Yamaha name does not claim a verified manufacturer model.
CORRECTIONS = {
    142: {"name": "Teclado Arranjador Yamaha 61 Teclas", "description_source_product_id": 144},
    144: {"description_source_product_id": 142, "specs": {"keys": "88"}, "warnings": {
        "en": "Catalogue adjustment. The key count was set to 88 to match the description. The exact Roland model remains unconfirmed, please confirm with the team.",
        "pt-BR": "Ajuste no catálogo. A quantidade de teclas foi definida como 88 para corresponder à descrição. O modelo exato da Roland ainda não foi confirmado, por favor, confirme com a equipe.",
    }},
}

# These conflicts remain unresolved. Do not turn either source into a verified fact.
CONFLICTS = {
    135: {"fields": ["brand", "model", "body"], "warnings": {
        "en": "Catalogue details conflict, please confirm with the team. The name says Music Man, but the description says Fender Jazz Bass. The description specifies Alder, while the body specification says Ash. Brand, model and body material are unconfirmed.",
        "pt-BR": "Há informações conflitantes no catálogo, por favor, confirme com a equipe. O nome informa Music Man, mas a descrição informa Fender Jazz Bass. A descrição indica Alder, enquanto a especificação do corpo indica Ash. Marca, modelo e material do corpo não estão confirmados.",
    }},
    137: {"fields": ["brand", "model", "strings"], "warnings": {
        "en": "Catalogue details conflict, please confirm with the team. The name says Yamaha, but the description says Ibanez with 5 strings, while the specifications say 4 strings. Brand, model and string count are unconfirmed. This is not a confirmed four-string or five-string recommendation.",
        "pt-BR": "Há informações conflitantes no catálogo, por favor, confirme com a equipe. O nome informa Yamaha, mas a descrição informa Ibanez com 5 cordas, enquanto as especificações informam 4 cordas. Marca, modelo e quantidade de cordas não estão confirmados. Este produto não é uma recomendação confirmada de baixo de quatro ou cinco cordas.",
    }},
    139: {"fields": ["brand", "model", "shells"], "warnings": {
        "en": "Catalogue details conflict, please confirm with the team. The name says Yamaha, but the description says Pearl Export with Poplar and Asian mahogany shells, while the specifications say Maple. Brand, model and shell materials are unconfirmed.",
        "pt-BR": "Há informações conflitantes no catálogo, por favor, confirme com a equipe. O nome informa Yamaha, mas a descrição informa Pearl Export com cascos em Poplar e mogno asiático, enquanto as especificações informam Maple. Marca, modelo e materiais dos cascos não estão confirmados.",
    }},
    140: {"fields": ["brand", "model", "shells"], "warnings": {
        "en": "Catalogue details conflict, please confirm with the team. The name says Pearl, but the description says Tama with Birch shells, while the specifications say Maple. Brand, model and shell material are unconfirmed.",
        "pt-BR": "Há informações conflitantes no catálogo, por favor, confirme com a equipe. O nome informa Pearl, mas a descrição informa Tama com cascos em Birch, enquanto as especificações informam Maple. Marca, modelo e material dos cascos não estão confirmados.",
    }},
}


def catalogue_warning(product_id, language="en"):
    record = CONFLICTS.get(int(product_id), CORRECTIONS.get(int(product_id), {}))
    return record.get("warnings", {}).get(language, "")


def corrected_products(rows):
    """Read donors from the original snapshot so a swap never overwrites its input."""
    originals = {int(row["product_id"]): row for row in rows}
    for row in rows:
        correction = CORRECTIONS.get(int(row["product_id"]), {})
        updated = dict(row)
        if "name" in correction:
            updated["name"] = correction["name"]
        if "description_source_product_id" in correction:
            updated["description"] = originals[correction["description_source_product_id"]]["description"]
        if "specs" in correction:
            updated["specs"] = json.dumps({**json.loads(row["specs"]), **correction["specs"]}, ensure_ascii=False)
        yield updated
