"""Narrow, source-backed policy answers, selected from the actual customer question."""
from emporio.data.catalog import normalize

# Key, topic, source pages, English, Brazilian Portuguese.
DETAILS = {
    "instalments": ("payments", [3],
        "Credit cards allow up to 12 interest-free instalments. Section 3.1 sets a R$80 minimum per instalment for 4–6 payments and R$100 for 7–12. For up to 3 payments it states no minimum except below R$50. The general payment table also states R$100, so please confirm the applicable minimum with the team before purchase.",
        "O cartão permite até 12 parcelas sem juros. A seção 3.1 informa parcela mínima de R$80 para 4–6 parcelas e R$100 para 7–12. Para até 3 parcelas, informa ausência de mínimo, exceto abaixo de R$50. A tabela geral também informa R$100, por isso confirme com a equipe o mínimo aplicável antes da compra."),
    "mixed_payment": ("payments", [3, 6],
        "Yes, the manual permits combined payment, such as PIX and card, for purchases above R$2,000. Our interpretation applies no 5% PIX discount to a mixed payment because the store does not receive the full amount via PIX. An otherwise eligible product promotion can still apply, without stacking. The manual does not specify the mixed-payment discount calculation, so please confirm the final arrangement with the team.",
        "Sim, o manual permite combinar pagamentos, como PIX e cartão, em compras acima de R$2.000. Pela nossa interpretação, o desconto PIX de 5% não se aplica ao pagamento misto, pois a loja não recebe o valor integral via PIX. Uma promoção válida do produto ainda pode ser aplicada, sem acumular descontos. O manual não define o cálculo do desconto no pagamento misto, por isso confirme a condição final com a equipe."),
    "pix_financing": ("payments", [3, 6],
        "If your bank finances the PIX in instalments but the store receives the full amount immediately via PIX, we apply the 5% PIX discount under our documented interpretation. Your bank's interest and fees are separate. We choose the better eligible single discount and never combine PIX with a product promotion.",
        "Se o banco parcela o PIX, mas a loja recebe o valor integral imediatamente via PIX, aplicamos o desconto PIX de 5% conforme nossa interpretação documentada. Juros e tarifas do banco são separados. Escolhemos o melhor desconto único aplicável, sem acumular PIX com promoção do produto."),
    "pix_discount": ("payments", [3, 6],
        "Full immediate PIX payment qualifies for 5% off the list price, with no minimum purchase stated. PIX and product promotions do not stack. We automatically choose the higher eligible single discount.",
        "O pagamento integral e imediato via PIX dá 5% de desconto sobre o preço de tabela, sem compra mínima informada. PIX e promoções não se acumulam. Escolhemos automaticamente o maior desconto único aplicável."),
    "refund": ("returns", [4],
        "For an eligible online return, the manual states a refund within 10 business days using the original payment method. It does not specify exactly when that processing period starts, so please confirm this with the team.",
        "Para uma devolução online elegível, o manual informa reembolso em até 10 dias úteis, pela mesma forma de pagamento original. O início exato desse prazo de processamento não está definido, por isso confirme com a equipe."),
    "return_conditions": ("returns", [4],
        "For an online change-of-mind return, request it within 7 calendar days after receipt, without needing a reason. The instrument must be unused, in its original packaging, with all supplied accessories and manuals. The store pays the return shipping. Please share the actual receipt date and item condition to assess eligibility.",
        "Para desistência de compra online, solicite a devolução em até 7 dias corridos após o recebimento, sem precisar justificar. O instrumento deve estar sem sinais de uso, na embalagem original e com todos os acessórios e manuais fornecidos. A loja paga o frete de devolução. Informe a data real de recebimento e o estado do item para avaliar as condições."),
    "exchange": ("returns", [4],
        "The manual allows preference exchanges within 7 days, subject to availability, with the instrument in perfect condition and its original packaging. Price differences are charged or refunded. Custom setups, items explicitly sold as final sale and wind-instrument mouthpieces are listed as ineligible. Please confirm how these conditions apply to your purchase.",
        "O manual permite troca por preferência em até 7 dias, conforme disponibilidade, com o instrumento em perfeito estado e na embalagem original. Diferenças de valor são cobradas ou reembolsadas. Regulagens sob encomenda, itens com aviso explícito de venda final e boquilhas são listados como não elegíveis. Confirme como essas condições se aplicam à sua compra."),
    "defect_exchange": ("returns", [4, 7],
        "The manual offers an exchange for a manufacturing defect within 30 calendar days after purchase. After that it directs customers to the manufacturer, with store assistance on request. It separately describes 90 days of legal coverage from receipt. Please ask the team to assess your case rather than treating the 30-day exchange period as the end of all coverage.",
        "O manual prevê troca por defeito de fabricação em até 30 dias corridos após a compra. Depois disso, orienta acionar o fabricante, com intermediação da loja mediante solicitação. Também descreve 90 dias de garantia legal a partir do recebimento. Peça à equipe uma avaliação do caso, sem considerar os 30 dias de troca como o fim de toda cobertura."),
    "warranty_exclusions": ("warranty", [7],
        "The manual excludes natural wear, misuse, falls, extreme climatic exposure, unauthorized modifications or repairs, and cosmetic damage that does not affect function. Please ask the team to assess the cause of a specific defect before a coverage decision.",
        "O manual exclui desgaste natural, mau uso, quedas, exposição a condições climáticas extremas, modificações ou reparos não autorizados e danos estéticos sem efeito no funcionamento. Peça à equipe uma avaliação da causa do defeito antes de decidir a cobertura."),
    "warranty_term": ("warranty", [7],
        "The manual describes 90 days of legal warranty for manufacturing defects from receipt. Manufacturer coverage varies, generally from 6 months to 2 years in the manual. The product's warranty certificate determines its specific manufacturer term, which I cannot confirm from the catalogue alone.",
        "O manual descreve 90 dias de garantia legal para defeitos de fabricação a partir do recebimento. A cobertura do fabricante varia, geralmente de 6 meses a 2 anos segundo o manual. O prazo específico consta no certificado do produto e não pode ser confirmado apenas pelo catálogo."),
    "special_shipping": ("delivery", [5],
        "Yes, large instruments such as acoustic drum kits, digital pianos and double basses may need special shipping with an individual quote. Please provide the destination postcode and exact instrument so the team can confirm the cost and arrangements.",
        "Sim, instrumentos de grande porte, como baterias acústicas, pianos digitais e contrabaixos, podem exigir frete especial com cotação individual. Informe o CEP de destino e o instrumento exato para a equipe confirmar o custo e as condições."),
    "carrier_times": ("delivery", [5],
        "Outside metropolitan Campo Grande, the manual estimates PAC at 5–12 business days, SEDEX at 2–5 and Jadlog at 3–8. All include tracking and insurance. These are estimates, not a promise for a specific order. Cost depends on destination postcode, weight and dimensions.",
        "Fora da região metropolitana de Campo Grande, o manual estima PAC em 5–12 dias úteis, SEDEX em 2–5 e Jadlog em 3–8. Todos incluem rastreamento e seguro. São estimativas, não garantia de prazo para um pedido específico. O custo depende do CEP, peso e dimensões."),
    "transit_damage": ("delivery", [5],
        "The manual says shipments include insurance against loss and transit damage. If the instrument arrives damaged, refuse receipt and contact the store immediately. I cannot register or settle the claim here.",
        "O manual informa seguro contra extravio e danos no transporte. Se o instrumento chegar avariado, recuse o recebimento e entre em contato com a loja imediatamente. Não posso registrar nem resolver a ocorrência por aqui."),
    "local_shipping": ("delivery", [4],
        "In metropolitan Campo Grande, delivery takes an estimated 1–3 business days. Shipping is free above R$500 and costs R$35 below R$500. Exactly R$500 is not defined, so please confirm that boundary with the team.",
        "Na região metropolitana de Campo Grande, a entrega é estimada em 1–3 dias úteis. O frete é grátis acima de R$500 e custa R$35 abaixo de R$500. O valor exato de R$500 não está definido, por isso confirme esse limite com a equipe."),
    "hours": ("store", [2],
        "We open Monday to Friday from 09:00 to 18:00 and Saturday from 09:00 to 13:00. We are closed on Sundays and holidays. WhatsApp follows the same staffed hours.",
        "Atendemos de segunda a sexta das 09:00 às 18:00 e aos sábados das 09:00 às 13:00. Fechamos aos domingos e feriados. O atendimento humano pelo WhatsApp segue o mesmo horário."),
}

def detail_keys(question):
    t = normalize(question)
    has = lambda *words: any(w in t for w in words)
    keys = []
    mixed = has("pix") and has("card", "cartao") and has("combin", "mix", "split", "part ", "parte", "divid", "remaining", "restante", "remainder", "%")
    if mixed:
        keys.append("mixed_payment")
    elif has("pix") and has("parcel", "instalm", "installm", "financ", "bank", "banco"):
        keys.append("pix_financing")
    elif has("instalm", "installm", "parcel"):
        keys.append("instalments")
    elif has("pix") and has("discount", "desconto", "promoc", "promotion", "5%"):
        keys.append("pix_discount")
    if has("refund", "reembolso", "estorno"):
        keys.append("refund")
    elif has("return", "devol", "arrepend"):
        keys.append("return_conditions")
    elif has("exchange", "troca"):
        keys.append("defect_exchange" if has("defect", "defeito") else "exchange")
    if has("warranty", "garantia"):
        keys.append("warranty_exclusions" if has("fall", "drop", "wear", "unauthor", "modif", "cover damage", "queda", "desgast", "reparo", "mau uso", "nao cobre", "exclu") else "warranty_term")
    if has("shipping", "delivery", "frete", "entrega", "transport"):
        if has("damage", "damaged", "avaria", "danific", "recusar"):
            keys.append("transit_damage")
        elif has("large", "special", "individual", "grande porte", "especial", "cotacao"):
            keys.append("special_shipping")
        elif has("pac", "sedex", "jadlog", "other cit", "outras cidad", "outside", "fora"):
            keys.append("carrier_times")
        else:
            keys.append("local_shipping")
    if has("opening", "hours", "saturday", "sunday", "horario", "sabado", "domingo"):
        keys.append("hours")
    return list(dict.fromkeys(keys))

def focused_policy(question):
    keys = detail_keys(question)
    if not keys:
        return None
    return {"focuses": keys, "summary": "\n\n".join(DETAILS[k][2] for k in keys),
            "summary_pt": "\n\n".join(DETAILS[k][3] for k in keys),
            "pages": sorted({p for k in keys for p in DETAILS[k][1]})}
