"""Deterministic English and Brazilian Portuguese presentation of trusted facts."""
import json
import re
from pathlib import Path

DESCRIPTIONS_EN = json.loads((Path(__file__).parents[1] / "data/descriptions_en.json").read_text(encoding="utf-8"))
CATEGORY_PT = {1:"Guitarras",2:"Contrabaixos",3:"Baterias e percussão",4:"Teclados e pianos",5:"Violões",6:"Sopros de madeira",7:"Metais",8:"Cordas de orquestra",9:"Ukuleles"}
WORDS_PT = {"Top":"Tampo","Back and sides":"Fundo e laterais","Neck":"Braço","Strings":"Cordas","Scale length":"Comprimento da escala","Electronics":"Eletrônica","Colour":"Cor","Body":"Corpo","Pickups":"Captadores","Pickup":"Captador","Frets":"Trastes","Keys":"Teclas","Type":"Tipo","Polyphony":"Polifonia","Size":"Tamanho","Fingerboard":"Escala","Bridge":"Ponte","Finish":"Acabamento","Black":"Preto","Red":"Vermelho","Blue":"Azul","Wine Red":"Vinho","steel":"aço","nylon":"nylon","yes":"sim","no":"não","active":"ativo","out of stock":"sem estoque","discontinued":"fora de linha","delivered":"entregue","shipped":"enviado","processing":"em processamento","pending":"pendente","cancelled":"cancelado"}
POLICIES_PT = {
"store":"A loja fica na Rua 14 de Maio, 3200, Centro, Campo Grande. Abre de segunda a sexta, das 09h às 18h, e aos sábados, das 09h às 13h. Fecha aos domingos e feriados. Os contatos divergem entre as seções do manual, por isso não posso confirmar um único telefone.",
"payments":"O PIX oferece 5% de desconto sobre o preço de tabela, sem valor mínimo informado. Promoções ativas e desconto PIX não se acumulam. O parcelamento no cartão depende do valor e do número de parcelas. O financiamento externo de um PIX é um acordo entre você e seu banco.",
"returns":"Para compras pela internet, o manual permite solicitar a devolução em até 7 dias corridos após o recebimento, conforme suas condições. Preciso saber o canal da compra, a data real de recebimento, o estado do produto e o motivo para avaliar o caso. A previsão de entrega não comprova o recebimento.",
"delivery":"O manual informa de 1 a 3 dias úteis para a região metropolitana de Campo Grande. Fora dessa região, prazo e valor dependem da transportadora e do destino. O frete local é grátis acima de R$500 e custa R$35 abaixo de R$500. O valor exato de R$500 não foi definido, então confirme com a equipe.",
"promotions":"Só se aplicam promoções marcadas como ativas nos dados fornecidos. Os descontos não se acumulam. Escolhemos o maior desconto individual aplicável e mostramos o preço original. Produtos sem estoque não estão disponíveis para compra.",
"warranty":"O manual informa 90 dias de garantia legal para defeitos de fabricação, contados do recebimento. A cobertura do fabricante varia. Não posso prometer um prazo específico para este produto sem o certificado de garantia.",
"privacy":"O manual limita o uso de dados pessoais ao atendimento, aos pedidos e às finalidades informadas. Marketing exige consentimento expresso. Este protótipo local verifica número do pedido e e-mail correspondente apenas para demonstração, não como autenticação de produção."
}
EXACT_PT = {
"I could not complete that request.":"Não consegui concluir essa solicitação.",
"I could not find that product in the supplied catalogue.":"Não encontrei esse produto no catálogo fornecido.",
"I could not find that order in the supplied data.":"Não encontrei esse pedido nos dados fornecidos.",
"Please choose a policy topic.":"Por favor, escolha um assunto sobre as regras da loja.",
"Choose a store policy topic.":"Escolha um assunto sobre as regras da loja.",
"I found no available instruments matching those filters. Try a higher budget or another category.":"Não encontrei instrumentos disponíveis com esses filtros. Tente aumentar o orçamento ou escolher outra categoria.",
"You can open the suggested catalogue view using the button below.":"Você pode abrir a seção sugerida do catálogo pelo botão abaixo.",
"Here is what I found.":"Veja o que encontrei.",
"Use the order lookup dialog with order number and matching email first.":"Primeiro, consulte o pedido pela janela de pedidos, usando o número e o e-mail correspondente.",
"This tool is not available.":"Esta ferramenta não está disponível.",
"Arguments do not match the documented tool schema.":"Os argumentos não correspondem ao formato documentado da ferramenta.",
"Choose a category or product to propose.":"Escolha uma categoria ou um produto para sugerir.",
"Unknown product.":"Produto desconhecido.",
"That product is in a different category.":"Esse produto pertence a outra categoria.",
"Recorded details":"Informações registradas",
"Ask the team for model-specific specifications.":"Peça à equipe as especificações deste modelo.",
"No technical specifications are recorded.":"Não há especificações técnicas registradas.",
"No sound-related specifications are recorded for this instrument.":"Não há especificações de som registradas para este instrumento.",
"Specifications cannot confirm its tone or playing feel. Please, ask the team about a listening demo or trying it in person.":"As especificações não confirmam o timbre nem a sensação ao tocar. Por favor, peça à equipe uma demonstração de som ou a possibilidade de experimentar o instrumento pessoalmente.",
"Hi, welcome to Empório da Música! Happy to help you find your next sound. Is there an instrument you have in mind?":"Olá, boas-vindas ao Empório da Música! Será um prazer ajudar você a encontrar seu próximo som. Tem algum instrumento em mente?",
"Hi again! Happy to help. What would you like to explore next?":"Olá de novo! Estou aqui para ajudar. O que você gostaria de explorar agora?",
"I'd be happy to help you look up an instrument, an order or a store policy. What would you like to explore?":"Será um prazer ajudar você a consultar um instrumento, um pedido ou uma regra da loja. O que gostaria de explorar?",
"This is the catalogue preview, not a connected AI model. I can show instruments by category or budget, quote a selected product, and look up store policies. Connect a model for free-form conversation.":"Esta é a prévia do catálogo, sem um modelo de IA conectado. Posso mostrar instrumentos por categoria ou orçamento, informar o preço de um produto selecionado e consultar as regras da loja. Conecte um modelo para conversar livremente."
}


def description(product, language="en"):
    return product["description"] if language == "pt-BR" else DESCRIPTIONS_EN.get(str(product["product_id"]), product["description"])


def product_for_language(product, language="en"):
    if not product:
        return product
    localized = {**product, "description": description(product, language), "language": language}
    values_en = {"Preto":"Black","Branco":"White","Vermelho":"Red","Azul":"Blue","Mogno":"Mahogany","Spruce Sólido":"Solid spruce","Spruce Engelmann Sólido":"Solid Engelmann spruce","Nato Sólido":"Solid Nato","Cedro":"Cedar"}
    localized["specs"] = {k: (WORDS_PT.get(v,v) if language == "pt-BR" else values_en.get(v,v)) for k,v in product["specs"].items()}
    if language == "pt-BR":
        localized["category_label"] = CATEGORY_PT[product["category_id"]]
    return localized


def translate(text, language="en"):
    if language != "pt-BR":
        return text
    if text in EXACT_PT:
        return EXACT_PT[text]
    patterns = [
        (r"The weight of (.+) is not recorded in the supplied catalogue\. Please ask the team to confirm it before purchase\.", lambda m: f"O peso de {m[1]} não está registrado no catálogo fornecido. Por favor, peça à equipe uma confirmação antes da compra."),
        (r"The recorded weight of (.+) is (.+)\. Please confirm it with the team before purchase\.", lambda m: f"O peso registrado de {m[1]} é {m[2]}. Por favor, confirme com a equipe antes da compra."),
        (r"I found (\d+) matching instrument(s?)\. The card(?:s)? below use(?:s)? prices and stock from the supplied catalogue\.", lambda m: f"Encontrei {m[1]} instrumento{'s' if m[2] else ''}. " + ("Os cartões abaixo mostram" if m[2] else "O cartão abaixo mostra") + " preços e estoque do catálogo fornecido."),
        (r"Here are the recorded sound and setup details for (.+)\.", lambda m: f"Estas são as informações de som e configuração registradas para {m[1]}."),
        (r"Here are the recorded specifications for (.+)\.", lambda m: f"Estas são as especificações registradas para {m[1]}."),
        (r"(.+) has (\d+) units? available in the supplied stock data\.", lambda m: f"{m[1]} tem {m[2]} unidade{'s' if m[2] != '1' else ''} disponível{'s' if m[2] != '1' else ''} nos dados de estoque fornecidos."),
        (r"(.+) is currently listed as (.+)\. I cannot confirm a purchase or replenishment date\.", lambda m: f"{m[1]} está registrado como {WORDS_PT.get(m[2],m[2])}. Não posso confirmar uma compra ou data de reposição."),
        (r"(.+) is (\d+) in stock\. The quoted price is (.+)", lambda m: f"{m[1]} tem {m[2]} em estoque. O preço informado é {m[3]}"),
        (r"(.+) is (out of stock|discontinued|inactive)\. The quoted price is (.+)", lambda m: f"{m[1]} está {WORDS_PT.get(m[2],m[2])}. O preço informado é {m[3]}"),
        (r"Order #(\d+) is recorded as (.+?) in the supplied snapshot\.(.*)", lambda m: f"O pedido #{m[1]} está registrado como {WORDS_PT.get(m[2],m[2])} nos dados fornecidos.{m[3]}"),
    ]
    lines=[]
    for line in text.split("\n"):
        if line in EXACT_PT:
            line=EXACT_PT[line]
        else:
            for pattern, replacement in patterns:
                match=re.fullmatch(pattern,line)
                if match:
                    line=replacement(match);break
            for en,pt in WORDS_PT.items():
                if line.startswith(en+": "):
                    value=line[len(en)+2:];line=pt+": "+WORDS_PT.get(value,value);break
        lines.append(line)
    text="\n".join(lines)
    text=re.sub(r" That is ([\d.]+)% off the (R\$ [\d,.]+) list price\.",r" Isso representa \1% de desconto sobre o preço de tabela de \2.",text)
    text=text.replace(" With full immediate PIX payment, the best single-discount price is "," Com pagamento integral e imediato via PIX, o melhor preço com um único desconto é ")
    text=text.replace(" Tracking reference: "," Código de rastreamento: ").replace(" No tracking reference is recorded."," Não há código de rastreamento registrado.")
    text=re.sub(r"R\$ ?([0-9,]+\.[0-9]{2})",lambda m:"R$ "+m[1].replace(",","_").replace(".",",").replace("_","."),text)
    return text
