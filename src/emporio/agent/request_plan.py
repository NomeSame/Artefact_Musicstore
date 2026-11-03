"""Bounded plans for explicit requests, separate from model guesses and prior UI state."""
import re
from emporio.data.catalog import normalize
from emporio.domain.advice import named_products, preferences_from_message
from emporio.domain.policy_details import detail_keys, DETAILS


def category_in(text):
    for cid,pattern in [(5,r'acoustic|violao|violoes'),(1,r'electric guitar|guitarra'),
                        (2,r'bass|baixo'),(3,r'drum|drums|bateria|percussion'),
                        (4,r'keys|piano|pianos|keyboard|teclado'),(6,r'woodwind|saxophone|saxofone'),
                        (7,r'brass|trumpet|trompete'),(8,r'violin|violino|orchestral'),(9,r'ukulele')]:
        if re.search(r'\b(?:'+pattern+r')\b',text):return cid
    return None


def plan_request(message, context, catalog):
    text=normalize(message)
    policies=detail_keys(message)
    policy=[('lookup_policy',{'topic':DETAILS[policies[0]][0]})] if policies else []
    orders=re.findall(r'\b(?:order|pedido)\s*#?\s*(\d+)\b',text)
    if orders and any(w in text for w in ('status','tracking','rastre','where','onde')):
        if len(set(orders))==1:
            return {'tools':[('get_order',{'order_id':int(orders[0])})]}
        return {'clarification': 'order'}
    products=catalog.search(limit=100)
    named=named_products(message,products)
    price=bool(re.search(r'\b(price|cost|quote|preco|custa|custo|how much is|quanto fica)\b',text))
    weight=bool(re.search(r'\b(weight|weigh|peso|pesa)\b',text))
    availability=bool(re.search(r'\b(available|buy|stock|discontinued|coming.soon|disponivel|comprar|estoque|descontinuado)\b',text))
    target=named[0] if len(named)==1 else context.get('selected_product_id') if not named else None
    category=category_in(text)
    if target and category and not named:
        selected=next((p for p in products if p['product_id']==target),None)
        if selected and selected['category_id']!=category:
            target=None
    payment_details={'mixed_payment','pix_financing','pix_discount','instalments','inactive_promotions'}
    product_price=price and (not policies or set(policies)<=payment_details or bool(named))
    if target and (product_price or weight or availability) and (not policies or product_price):
        payment=context.get('payment','unspecified')
        if 'pix' in text:
            payment='card' if 'mixed_payment' in policies else 'pix'
        focus='weight' if weight else 'price' if price else 'availability'
        return {'tools':[('get_product',{'product_id':target,'focus':focus,'payment':payment}),*policy]}
    if policy:
        return {'tools':policy}
    search=bool(re.search(r'\b(which|find|show|available|quais|mostr|encontr|disponiveis)\b',text))
    if category and search and not named and not context.get('selected_product_id'):
        # Preserve an explicitly named brand. Do not turn instrument-type words
        # into literal English search tokens against Portuguese descriptions.
        brands={normalize(p['name']).split()[0] for p in products}
        query=' '.join(sorted(b for b in brands if re.search(r'\b'+re.escape(b)+r'\b',text)))
        budget=preferences_from_message(message).get('max_price',context.get('max_price'))
        return {'tools':[('search_products',{'query':query,'category_id':category,'max_price':budget,
                                            'available_only':True,'payment':context.get('payment','unspecified')})]}
    if price and not target and (category or context.get('category_id') or len(context.get('visible_product_ids',[]))>1):
        return {'clarification':'product'}
    return None
