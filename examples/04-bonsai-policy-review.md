# Bonsai27B policy review

This is an actual local model conversation recorded on 3 November 2026 through the existing llama.cpp and llama-swap endpoint. The selected model ID was Bonsai27B. The application retained one conversation while the evaluator changed the selected instrument and later switched the site language from English to Brazilian Portuguese. These are prepared evaluation questions, not an independent customer study.

Twelve of twelve cases passed the recorded checks for requested details, excluded unrelated facts, absence of unsolicited product cards and consultation of the manual. In two Portuguese turns, combined payment and special shipping, the model omitted the policy tool. The application recognized those supported detail questions and performed the logged manual lookup before rendering the answer. The other turns used model-selected tools and source evidence. The application produced the visible factual replies through its controlled renderer. The first case included an extra product lookup by the model, which did not appear as an unsolicited overview or card. This result evaluates the combined application and model, not the model in isolation.

The mixed-payment discount rule and treatment of externally financed PIX are documented project interpretations. The manual permits combined payment above R$2,000 but does not define that discount calculation. The instalment reply preserves the conflict between the general table and the more specific rules rather than silently choosing one.

The reproducible runner is `scripts/check_policy_model.py`. Its default output folder is `.runtime/bonsai-policy-evaluation`, which contains complete model requests and responses in `model-requests.json` and application replies and checks in `results.json`. Those local diagnostic files are ignored by Git. The selected model needs to be available on the configured endpoint, and the runner performs real inference. No injection tests are included in this review.

## Turn 1

Selected catalogue product 81. The active site language was en. The application turn took 25.19 seconds.

**Customer**

Can I pay for this instrument in 12 credit card installments without interest, and what is the minimum installment?

**Emp?rio Guide**

Credit cards allow up to 12 interest-free instalments. Section 3.1 sets a R$80 minimum per instalment for 4–6 payments and R$100 for 7–12. For up to 3 payments it states no minimum except below R$50. The general payment table also states R$100, so please confirm the applicable minimum with the team before purchase.

## Turn 2

Selected catalogue product 135. The active site language was en. The application turn took 10.08 seconds.

**Customer**

For an order above R$2000, can I combine PIX and credit card?

**Emp?rio Guide**

Yes, the manual permits combined payment, such as PIX and card, for purchases above R$2,000. Our interpretation applies no 5% PIX discount to a mixed payment because the store does not receive the full amount via PIX. An otherwise eligible product promotion can still apply, without stacking. The manual does not specify the mixed-payment discount calculation, so please confirm the final arrangement with the team.

## Turn 3

Selected catalogue product 81. The active site language was en. The application turn took 15.45 seconds.

**Customer**

If my bank offers PIX in installments and the store gets the full amount immediately, do I get the PIX discount?

**Emp?rio Guide**

If your bank finances the PIX in instalments but the store receives the full amount immediately via PIX, we apply the 5% PIX discount under our documented interpretation. Your bank's interest and fees are separate. We choose the better eligible single discount and never combine PIX with a product promotion.

## Turn 4

Selected catalogue product 131. The active site language was en. The application turn took 9.14 seconds.

**Customer**

For an online return, how long does the refund take and which payment method is used?

**Emp?rio Guide**

For an eligible online return, the manual states a refund within 10 business days using the original payment method. It does not specify exactly when that processing period starts, so please confirm this with the team.

## Turn 5

Selected catalogue product 142. The active site language was en. The application turn took 7.21 seconds.

**Customer**

Does the warranty cover damage from a fall or unauthorized repairs?

**Emp?rio Guide**

The manual excludes natural wear, misuse, falls, extreme climatic exposure, unauthorized modifications or repairs, and cosmetic damage that does not affect function. Please ask the team to assess the cause of a specific defect before a coverage decision.

## Turn 6

Selected catalogue product 139. The active site language was en. The application turn took 23.91 seconds.

**Customer**

Can delivery of a large instrument require a special individual shipping quote?

**Emp?rio Guide**

Yes, large instruments such as acoustic drum kits, digital pianos and double basses may need special shipping with an individual quote. Please provide the destination postcode and exact instrument so the team can confirm the cost and arrangements.

## Turn 7

Selected catalogue product 121. The active site language was en. The application turn took 14.29 seconds.

**Customer**

What PIX discount is offered and can I stack it with a promotion?

**Emp?rio Guide**

Full immediate PIX payment qualifies for 5% off the list price, with no minimum purchase stated. PIX and product promotions do not stack. We automatically choose the higher eligible single discount.

## Turn 8

Selected catalogue product 142. The active site language was en. The application turn took 8.54 seconds.

**Customer**

What are your opening hours on Saturday and are you closed on Sundays?

**Emp?rio Guide**

We open Monday to Friday from 09:00 to 18:00 and Saturday from 09:00 to 13:00. We are closed on Sundays and holidays. WhatsApp follows the same staffed hours.

## Turn 9

Selected catalogue product 81. The active site language was pt-BR. The application turn took 6.93 seconds.

**Customer**

Posso combinar parte em PIX e parte no cartão em uma compra acima de R$2.000?

**Emp?rio Guide**

Sim, o manual permite combinar pagamentos, como PIX e cartão, em compras acima de R$2.000. Pela nossa interpretação, o desconto PIX de 5% não se aplica ao pagamento misto, pois a loja não recebe o valor integral via PIX. Uma promoção válida do produto ainda pode ser aplicada, sem acumular descontos. O manual não define o cálculo do desconto no pagamento misto, por isso confirme a condição final com a equipe.

## Turn 10

Selected catalogue product 131. The active site language was pt-BR. The application turn took 8.44 seconds.

**Customer**

Em quantos dias recebo o reembolso e por qual forma de pagamento?

**Emp?rio Guide**

Para uma devolução online elegível, o manual informa reembolso em até 10 dias úteis, pela mesma forma de pagamento original. O início exato desse prazo de processamento não está definido, por isso confirme com a equipe.

## Turn 11

Selected catalogue product 139. The active site language was pt-BR. The application turn took 31.48 seconds.

**Customer**

Uma bateria grande pode precisar de frete especial com cotação individual?

**Emp?rio Guide**

Sim, instrumentos de grande porte, como baterias acústicas, pianos digitais e contrabaixos, podem exigir frete especial com cotação individual. Informe o CEP de destino e o instrumento exato para a equipe confirmar o custo e as condições.

## Turn 12

Selected catalogue product 81. The active site language was pt-BR. The application turn took 42.28 seconds.

**Customer**

O PIX parcelado pelo banco tem desconto se a loja recebe o valor integral imediatamente?

**Emp?rio Guide**

Se o banco parcela o PIX, mas a loja recebe o valor integral imediatamente via PIX, aplicamos o desconto PIX de 5% conforme nossa interpretação documentada. Juros e tarifas do banco são separados. Escolhemos o melhor desconto único aplicável, sem acumular PIX com promoção do produto.
