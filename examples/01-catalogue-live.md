# Catalogue prices, discounts and availability

This is an actual conversation from the final functional acceptance on 3 November 2026. The configured local model was Bonsai27B at `http://127.0.0.1:8080/v1`. The server reported Bonsai-27B-Q1_0.gguf with very high reasoning effort. Its settings were not changed. Questions were prepared for evaluation rather than collected from independent customers.

Each group used its own real application session through FastAPI routes and the live model provider. The model selected tools, while the application validated the request evidence and produced the visible factual replies. Direct application clarifications and API verification events are identified separately. This evaluates the application with the model and does not attribute every correct sentence to free model generation.

This conversation contains 9 chat turns and 0 API events. It made 7 provider calls. All its recorded checks passed. The complete run passed 24 steps across three sessions, including independently calculated CSV price expectations.

The report revision label is `64da508+acceptance-fixes`. It describes a working tree based on the stated commit, not a new commit ID. The exact application hashes, actual replies, checks and model requests are recorded under `.runtime/model-acceptance-verified`. Earlier failed attempts remain in separate runtime folders. The reproducible runner is `scripts/check_model_acceptance.py`. This was functional acceptance, and the separate final injection campaign is still open.

## C01

The site language was en, with payment setting unspecified. This turn made 1 provider calls and took 4.91 seconds.

**Customer**

Which acoustic guitars are available under R$1000?

**Empório Guide**

I found 12 matching instruments. The cards below use prices and stock from the supplied catalogue.

The interface displayed these product cards.

- Yamaha C40 Nylon Natural, R$ 599.90, available.
- Yamaha C70 Nylon Natural, R$ 849.00, available.
- Tagima Memphis AC-39 Nylon Natural, R$ 429.90, available.
- Giannini GN-15 Nylon Cedr Natural, R$ 689.00, available.
- Rozini RC-104 Nylon Estudante, R$ 459.90, available.
- Tagima Dallas Tuner Aço Natural, R$ 749.00, available.
- Yamaha F310 Aço Natural, R$ 699.90, available.
- Giannini GF-1R Aço Folk Sunburst, R$ 579.90, available.
- Shelby SN-100 Folk Aço Preto, R$ 549.00, available.
- Tagima Woodstock Dreadnought Natural, R$ 899.00, available.
- Shelby SGD-195E Elétrico Aço Sunburst, R$ 799.00, available.
- Tagima TW-7 7 Cordas Aço Natural, R$ 999.00, available.

Recorded tools were `search_products`.

## C02

The site language was en, with selected product 81, payment setting pix. This turn made 1 provider calls and took 13.58 seconds.

**Customer**

What does this instrument cost with full immediate PIX payment?

**Empório Guide**

Yamaha C40 Nylon Natural is 12 in stock. The quoted price is R$ 569.91. That is 5% off the R$ 599.90 list price.

The interface displayed these product cards.

- Yamaha C40 Nylon Natural, R$ 569.91, available.

Recorded tools were `get_product`.

## C03

The site language was en, with selected product 90, payment setting pix. This turn made 1 provider calls and took 40.59 seconds.

**Customer**

What is the price of this instrument with PIX when its active promotion also applies?

**Empório Guide**

Crafter HT-100 Folk Aço Natural is 3 in stock. The quoted price is R$ 1,967.18. That is 18% off the R$ 2,399.00 list price.

Full immediate PIX payment qualifies for 5% off the list price, with no minimum purchase stated. PIX and product promotions do not stack. We automatically choose the higher eligible single discount.

The interface displayed these product cards.

- Crafter HT-100 Folk Aço Natural, R$ 1,967.18, available.

Recorded tools were `get_product`, `lookup_policy`.

## C04

The site language was en, with selected product 102, payment setting pix. This turn made 1 provider calls and took 44.09 seconds.

**Customer**

What is the current PIX price of this instrument? Does an inactive promotion apply?

**Empório Guide**

Crafter CE-15 Elétrico Nylon Natural is 2 in stock. The quoted price is R$ 3,704.05. That is 5% off the R$ 3,899.00 list price.

Full immediate PIX payment qualifies for 5% off the list price, with no minimum purchase stated. PIX and product promotions do not stack. We automatically choose the higher eligible single discount.

Inactive or expired promotions do not apply. I use only promotions marked active in the supplied snapshot. The current product quote determines the applicable single discount, without stacking.

The interface displayed these product cards.

- Crafter CE-15 Elétrico Nylon Natural, R$ 3,704.05, available.

Recorded tools were `get_product`, `lookup_policy`.

## C05

The site language was en, with selected product 90, payment setting pix. This turn made 1 provider calls and took 4.53 seconds.

**Customer**

What is the price if I split payment between PIX and card, rather than paying the full amount by PIX?

**Empório Guide**

Crafter HT-100 Folk Aço Natural is 3 in stock. The quoted price is R$ 1,967.18. That is 18% off the R$ 2,399.00 list price.

Yes, the manual permits combined payment, such as PIX and card, for purchases above R$2,000. Our interpretation applies no 5% PIX discount to a mixed payment because the store does not receive the full amount via PIX. An otherwise eligible product promotion can still apply, without stacking. The manual does not specify the mixed-payment discount calculation, so please confirm the final arrangement with the team.

The interface displayed these product cards.

- Crafter HT-100 Folk Aço Natural, R$ 1,967.18, available.

Recorded tools were `lookup_policy`, `get_product`.

## C06

The site language was en, with selected product 96, payment setting unspecified. This turn made 0 provider calls and took 0.01 seconds.

**Customer**

Is this instrument available to buy, and when will it be back in stock?

**Empório Guide**

Giannini GF-3D Dreadnought Sunburst is currently listed as out of stock. I cannot confirm a purchase or replenishment date.

The interface displayed these product cards.

- Giannini GF-3D Dreadnought Sunburst, R$ 799.90, unavailable.

Recorded tools were `get_product`.

## C07

The site language was en, with selected product 136, payment setting unspecified. This turn made 0 provider calls and took 0.01 seconds.

**Customer**

Can I buy this instrument even if its status is discontinued?

**Empório Guide**

Ibanez Bass 2X Electric Bass is currently listed as discontinued. I cannot confirm a purchase or replenishment date.

The interface displayed these product cards.

- Ibanez Bass 2X Electric Bass, R$ 441.00, unavailable.

Recorded tools were `get_product`.

## C08

The site language was en, with selected product 130, payment setting unspecified. This turn made 0 provider calls and took 0.01 seconds.

**Customer**

Is this coming-soon instrument already available to buy?

**Empório Guide**

Kala KA-ABP-CTG Barítono Cedar is currently listed as coming soon. I cannot confirm a purchase or replenishment date.

The interface displayed these product cards.

- Kala KA-ABP-CTG Barítono Cedar, R$ 1,749.00, unavailable.

Recorded tools were `get_product`.

## C09

The site language was en, with payment setting unspecified. This turn made 2 provider calls and took 21.01 seconds.

**Customer**

Do you have an Acme Dragon 999 guitar in your catalogue?

**Empório Guide**

I found no available instruments matching those filters. Try a higher budget or another category.

Recorded tools were `search_products`.
