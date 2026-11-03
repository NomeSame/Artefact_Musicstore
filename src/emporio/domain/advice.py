"""Bounded instrument comparisons with explicit preferences and catalogue evidence."""
import re
from emporio.data.catalog import normalize
from emporio.domain.language import product_for_language
from emporio.domain.pricing import cents


def advice_intent(message):
    return bool(re.search(r"\b(compare|comparison|versus|vs|better|best|cheaper|cheapest|recommend|recommendation|which.*(?:choose|suits|fits)|comparar|comparacao|melhor|mais barato|mais barata|recomenda|recomendacao|qual.*(?:escolh|combina))\b", normalize(message)))


def advice_focus(message):
    t = normalize(message)
    if re.search(r'\b(comfort|comfortable|easier|playability|conforto|confortavel|facil|tocabilidade)\b', t):
        return 'feel'
    if re.search(r'\b(tone|sound|timbre|som)\b', t):
        return 'sound'
    if re.search(r'\b(weight|lighter|portable|portability|peso|leve|portabilidade)\b', t):
        return 'portability'
    return 'overall'


def preferences_from_message(message):
    """Only explicit bounded choices enter state, not model-invented preferences."""
    text = normalize(message)
    prefs = {}
    amount = re.search(r"(?:budget(?:\s+is|\s+of)?|orcamento(?:\s+de|\s+e)?|can spend|posso gastar|under|below|up to|ate|maximo(?:\s+de)?)\s*(?:r\$\s*)?([\d][\d.,]*)", text)
    if amount:
        value = amount.group(1).rstrip('.,')
        # Accept 1,000.50 / 1.000,50 and common whole-thousand separators.
        if ',' in value and '.' in value:
            decimal = ',' if value.rfind(',') > value.rfind('.') else '.'
            value = value.replace('.' if decimal == ',' else ',', '').replace(decimal, '.')
        elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", value):
            value = value.replace(',', '').replace('.', '')
        else:
            value = value.replace(',', '.')
        amount_value = float(value)
        if 0 <= amount_value <= 10000000:
            prefs['max_price'] = amount_value
    if re.search(r"\b(no budget limit|no price limit|sem limite de (?:preco|orcamento))\b", text):
        prefs['max_price'] = None
    negated_strings = re.search(r"\b(?:not want|don't want|nao quero|nao prefiro|not prefer|don't prefer)\b", text)
    strings = re.search(r"\b(?:want|prefer|need|quero|prefiro|preciso)(?:\s+(?!(?:nylon|steel|aco)\b)\w+){0,3}\s+(nylon|steel|aco)\b", text)
    if not negated_strings and strings:
        prefs['string_type'] = 'nylon' if strings.group(1) == 'nylon' else 'steel'
    if re.search(r"\b(either string|no string preference|sem preferencia de cordas)\b", text):
        prefs['string_type'] = None
    if re.search(r"\b(?:need|want|preciso|quero).{0,35}\b(?:amplif|plug|eletronic|electronics)", text):
        prefs['electronics'] = True
    if re.search(r"\b(?:don't want|do not want|without|no|nao quero|sem).{0,30}\b(?:amplif|plug|eletronic|electronics)", text):
        prefs['electronics'] = False
    if re.search(r"\b(?:do not need|don't need|no need|nao preciso).{0,30}\b(?:amplif|plug|eletronic|electronics)", text):
        prefs['electronics'] = None
    if re.search(r"\b(beginner|first instrument|first guitar|iniciante|primeiro instrumento|primeiro violao)\b", text):
        prefs['beginner'] = True
    if re.search(r"\b(not (?:a )?beginner|nao sou iniciante)\b", text):
        prefs['beginner'] = False
    for value, pattern in [('home', r'home|practice at home|em casa'), ('stage', r'on stage|live gigs|palco|ao vivo'), ('recording', r'recording|record music|gravar|gravacao')]:
        if re.search(rf'\b(?:{pattern})\b', text):
            prefs['use_case'] = value
    return prefs


def named_products(message, products):
    text = normalize(message)
    explicit = [int(i) for i in re.findall(r'\b(?:id|product|produto)\s*#?\s*(\d+)\b', text)]
    numeric_pair = re.search(r'\b(?:compare|comparar|comparacao entre)\s+(\d+)\s+(?:and|e|vs\.?|versus)\s+(\d+)\b', text)
    if numeric_pair:
        explicit.extend(map(int, numeric_pair.groups()))
    if explicit:
        # Preserve invalid IDs so the tool reports them instead of substituting another model.
        return list(dict.fromkeys(explicit))
    token_sets = {p['product_id']: set(re.findall(r'[a-z0-9][a-z0-9-]{2,}', normalize(p['name']))) for p in products}
    counts = {}
    for tokens in token_sets.values():
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
    found = []
    for p in products:
        name = normalize(p['name'])
        unique_match = any(counts[t] == 1 and (any(c.isdigit() for c in t) or
                           t in {'stratocaster', 'telecaster', 'les', 'nautilus'}) and
                           re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', text)
                           for t in token_sets[p['product_id']])
        if name in text or unique_match:
            found.append(p['product_id'])
    return found


def compare(catalog, product_ids, max_price=None, string_type=None, electronics=None, beginner=False, use_case=None, focus='overall', payment='unspecified'):
    if len(set(product_ids)) != len(product_ids):
        return {'error': 'duplicate_products', 'message': 'Please choose different instruments to compare.'}
    products = [catalog.product(i, payment=payment) for i in product_ids]
    if any(p is None for p in products):
        return {'error': 'not_found', 'message': 'A comparison product is not in the supplied catalogue.'}
    requirements = {'max_price': max_price, 'string_type': string_type, 'electronics': electronics, 'beginner': beginner, 'use_case': use_case}
    assessments = []
    for p in products:
        checks = {'available': p['available']}
        if p.get('catalogue_conflict'):
            checks['catalogue_details'] = None
        if max_price is not None:
            checks['budget'] = p['price_cents'] <= cents(max_price)
        if string_type:
            recorded = normalize(p['specs'].get('strings', ''))
            checks['string_type'] = recorded == string_type if recorded in {'nylon', 'steel'} else None
        if electronics is not None:
            recorded = normalize(p['specs'].get('electronics', ''))
            checks['electronics'] = (recorded == 'yes') == electronics if recorded in {'yes', 'no'} else None
        assessments.append({'product_id': p['product_id'], 'checks': checks})
    return {'found': True, 'products': products, 'requirements': requirements, 'assessments': assessments,
            'snapshot': True, 'source': 'supplied catalogue', 'payment': payment, 'focus': focus}


def render_comparison(result, language='en'):
    pt = language == 'pt-BR'
    if result.get('error'):
        return ('Por favor, escolha dois ou três instrumentos diferentes do catálogo para comparar.' if pt
                else 'Please choose two or three different catalogue instruments to compare.')
    products = [product_for_language(p, language) for p in result['products']]
    prefs = result['requirements']
    focus = result.get('focus', 'overall')
    if focus != 'overall':
        names = ', '.join(p['name'] for p in products)
        if focus == 'feel':
            return (f'Para {names}, o catálogo não informa ação, perfil do braço ou conforto. Não posso afirmar qual é mais fácil de tocar. Por favor, experimente os instrumentos com ajuda da equipe. Qual dificuldade de conforto você quer evitar?' if pt else
                    f'For {names}, the catalogue does not record action, neck profile or comfort. I cannot confirm which is easier to play. Please try the instruments with the team. What comfort issue would you like to avoid?')
        if focus == 'portability':
            return (f'O peso de {names} não está registrado. Não posso confirmar qual é mais leve. Você precisa transportar o instrumento com frequência? Peça à equipe os pesos e dimensões antes de decidir.' if pt else
                    f'The weight of {names} is not recorded. I cannot confirm which is lighter. Will you carry the instrument often? Please ask the team for weights and dimensions before deciding.')
        return (f'Para {names}, os materiais registrados não comprovam o timbre. Não posso afirmar qual soa melhor ou qual combina mais com um estilo. Por favor, peça uma demonstração lado a lado. Que tipo de som você procura?' if pt else
                f'For {names}, recorded materials do not establish tone. I cannot confirm which sounds better or suits a style more. Please ask for a side-by-side demo. What kind of sound are you looking for?')
    def money(cents):
        value = f'{cents/100:,.2f}'
        if pt:
            value = value.replace(',', '_').replace('.', ',').replace('_', '.')
        return 'R$ ' + value
    parts = ['Posso comparar os dados registrados e explicar o que eles permitem concluir.' if pt
             else 'Happy to compare the recorded facts and explain what they support.']
    if prefs.get('use_case'):
        uses = {'home': ('tocar em casa', 'playing at home'), 'stage': ('tocar ao vivo', 'playing live'), 'recording': ('gravar', 'recording')}
        use = uses[prefs['use_case']][0 if pt else 1]
        parts.append(f'Você mencionou {use}. Vou considerar os requisitos verificáveis, sem presumir timbre ou conforto.' if pt else
                     f'You mentioned {use}. I will use the requirements we can verify, without assuming tone or comfort.')
    # Prefer differences, not complete specification dumps. Omitted fields are unknown.
    fields = ['strings', 'electronics', 'scale', 'keys', 'body', 'neck', 'top']
    different = [k for k in fields if len({str(p['specs'].get(k, '')) for p in products}) > 1]
    chosen = list(dict.fromkeys((['strings'] if prefs.get('string_type') else []) +
                                (['electronics'] if prefs.get('electronics') is not None else []) + different))[:3]
    labels = {'strings': ('cordas', 'strings'), 'electronics': ('eletrônica', 'electronics'),
              'scale': ('escala', 'scale length'), 'keys': ('teclas', 'keys'),
              'body': ('corpo', 'body'), 'neck': ('braço', 'neck'), 'top': ('tampo', 'top')}
    for p in products:
        availability = ('disponível' if p['available'] else 'indisponível') if pt else ('available' if p['available'] else 'unavailable')
        details = []
        for key in chosen:
            val = p['specs'].get(key)
            if key in p.get('unconfirmed_fields', []):
                val = 'não confirmado' if pt else 'unconfirmed'
            val = str(val) if val is not None else ('não informado' if pt else 'not recorded')
            details.append(f'{labels[key][0 if pt else 1]} {val}')
        parts.append(f"{p['name']} — {money(p['price_cents'])}, {availability}." + (' ' + ', '.join(details) + '.' if details else ''))
    amounts = [p['price_cents'] for p in products]
    if len(set(amounts)) > 1:
        low = min(products, key=lambda p: p['price_cents'])
        high = max(products, key=lambda p: p['price_cents'])
        parts.append((f"{low['name']} custa {money(high['price_cents']-low['price_cents'])} menos que {high['name']}. Isso é uma diferença de preço, não uma prova de maior qualidade." if pt else
                      f"{low['name']} costs {money(high['price_cents']-low['price_cents'])} less than {high['name']}. That is a price difference, not evidence of better quality."))
    constrained = any(prefs.get(k) is not None for k in ('max_price', 'string_type', 'electronics'))
    names = {p['product_id']: p['name'] for p in products}
    eligible = [a for a in result['assessments'] if all(v is True for v in a['checks'].values())]
    for a in result['assessments']:
        name = names[a['product_id']]
        for criterion, valid in a['checks'].items():
            if criterion == 'available' or valid is True:
                continue
            if valid is None:
                if criterion == 'catalogue_details':
                    parts.append((f'Para {name}, confirme os dados conflitantes com a equipe antes de considerar uma recomendação.' if pt else
                                  f'For {name}, please confirm the conflicting details with the team before treating it as a recommendation.'))
                    continue
                reason = ('A informação necessária sobre cordas ou eletrônica não está registrada.' if pt else
                          'The required string or electronics detail is not recorded.')
                parts.append((f'Para {name}, ' if pt else f'For {name}, ') + reason[0].lower() + reason[1:])
                continue
            else:
                reasons = {'budget': ('excede seu orçamento', 'exceeds your budget'),
                           'string_type': ('não tem a corda solicitada nos dados', 'does not have your requested string type in the record'),
                           'electronics': ('não atende sua preferência de eletrônica nos dados', 'does not match your stated electronics preference in the record')}
                reason = reasons[criterion][0 if pt else 1] + '.'
            parts.append(f'{name} {reason}')
    if constrained and len(eligible) == 1:
        candidate = names[eligible[0]['product_id']]
        parts.append((f"Entre estes instrumentos, {candidate} é o único com disponibilidade e atendimento aos requisitos confirmados nos dados. Eu começaria por ele com base nesses critérios, sujeito à confirmação dos dados e a um teste em pessoa." if pt else
                      f"Among these instruments, {candidate} is the only one with availability and a match to your stated requirements confirmed in the data. I would start with that option on those criteria, subject to confirming the record and trying it in person."))
    elif constrained and not eligible:
        parts.append('Nenhum destes instrumentos tem atendimento completo aos seus requisitos confirmado. Quer procurar alternativas?' if pt else
                     'None of these instruments has a confirmed match to all your requirements. Would you like to look for alternatives?')
    else:
        parts.append('Os dados não justificam escolher um como melhor para você ainda.' if pt else
                     'The recorded facts do not yet justify calling one the better fit for you.')
    questions = []
    if prefs.get('max_price') is None:
        questions.append('Qual é seu orçamento máximo?' if pt else 'What is your maximum budget?')
    if prefs.get('electronics') is None and all(p['category_id'] == 5 for p in products):
        questions.append('Você precisa de eletrônica integrada para amplificação?' if pt else 'Do you need built-in electronics for amplification?')
    elif not constrained:
        questions.append('O que mais importa para você e onde pretende tocar?' if pt else 'What matters most to you, and where will you play?')
    if questions and (not constrained or len(eligible) > 1):
        parts.append(' '.join(questions[:2]))
    parts.append(('O catálogo não confirma timbre, conforto, ação das cordas ou peso. ' + ('Como iniciante, peça ajuda para experimentar os instrumentos antes de decidir.' if prefs.get('beginner') else 'Por favor, peça uma demonstração e experimente antes de decidir.')) if pt else
                 ('The catalogue cannot confirm tone, comfort, action or weight. ' + ('As a beginner, please ask for help trying the instruments before deciding.' if prefs.get('beginner') else 'Please ask for a demo and try them before deciding.')))
    return '\n\n'.join(parts)
