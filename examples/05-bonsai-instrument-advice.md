# Bonsai27B instrument advice review

This is the actual final evaluation conversation recorded on 3 November 2026 on `feature/instrument-advice`. The local endpoint selected Bonsai27B, and the running server reported Bonsai-27B-Q1_0.gguf with very high reasoning effort. Those server settings were read without changing them. These are prepared evaluation questions, not a customer study.

All ten final application cases passed their recorded checks for product selection, required facts, excluded claims and source tools. There were 9 provider calls. Three focused follow-ups about comfort, tone and weight used the direct catalogue path and made no model call. The remaining seven turns used the actual model endpoint. No connection failure occurred in this final run. The model selects tools, while the application validates the comparison and writes the visible factual answer.

Earlier runs are retained locally and were not successful. One reached the six-round limit after repeatedly filtering out an over-budget comparison candidate. Others reached the provider timeout. The revised comparison keeps explicitly named candidates even if they exceed the budget, restricts the model tools and completes the assessment after one model round. The application has an explicitly labelled catalogue fallback for connection errors, which is covered separately by an automated test and was not needed in this final run.

The conversation keeps the comparison and explicit preferences across turns. It changes the preferred string type and budget, adds a requirement that neither initial candidate satisfies, introduces a new pair and switches the site to Brazilian Portuguese. It ends with two English policy questions to check that comparison state does not add unsolicited product facts. This covers bounded comparison assistance, not unrestricted genre or tone expertise.

The opt-in runner is `scripts/check_advice_model.py`. The exact final records are in `.runtime/bonsai-advice-reviewed/results.json` and `model-requests.json`. Earlier attempts remain separately under `.runtime/bonsai-advice-evaluation`, `.runtime/bonsai-advice-final`, `.runtime/bonsai-advice-verified` and `.runtime/bonsai-advice-release`. Runtime files are ignored by Git. The runner exits unsuccessfully on a model connection failure even when the catalogue fallback satisfies its functional checks.

## Turn 1

The site language was en. This turn made 1 provider calls and took 30.13 seconds.

**Customer**

Compare Yamaha C40 and Yamaha F310. Which is better for me?

**Empório Guide**

Happy to compare the recorded facts and explain what they support.

Yamaha C40 Nylon Natural — R$ 599.90, available. strings nylon, scale length 650mm.

Yamaha F310 Aço Natural — R$ 699.90, available. strings steel, scale length 634mm.

Yamaha C40 Nylon Natural costs R$ 100.00 less than Yamaha F310 Aço Natural. That is a price difference, not evidence of better quality.

The recorded facts do not yet justify calling one the better fit for you.

What is your maximum budget? Do you need built-in electronics for amplification?

The catalogue cannot confirm tone, comfort, action or weight. Please ask for a demo and try them before deciding.

## Turn 2

The site language was en. This turn made 1 provider calls and took 7.18 seconds.

**Customer**

I am a beginner. My budget is R$650 and I prefer nylon strings. I will play at home.

**Empório Guide**

Happy to compare the recorded facts and explain what they support.

You mentioned playing at home. I will use the requirements we can verify, without assuming tone or comfort.

Yamaha C40 Nylon Natural — R$ 599.90, available. strings nylon, scale length 650mm.

Yamaha F310 Aço Natural — R$ 699.90, available. strings steel, scale length 634mm.

Yamaha C40 Nylon Natural costs R$ 100.00 less than Yamaha F310 Aço Natural. That is a price difference, not evidence of better quality.

Yamaha F310 Aço Natural exceeds your budget.

Yamaha F310 Aço Natural does not have your requested string type in the record.

Among these instruments, Yamaha C40 Nylon Natural is the only one with availability and a match to your stated requirements confirmed in the data. I would start with that option on those criteria, subject to confirming the record and trying it in person.

The catalogue cannot confirm tone, comfort, action or weight. As a beginner, please ask for help trying the instruments before deciding.

## Turn 3

The site language was en. This turn made 1 provider calls and took 6.36 seconds.

**Customer**

Actually, I prefer steel strings and my budget is R$800.

**Empório Guide**

Happy to compare the recorded facts and explain what they support.

You mentioned playing at home. I will use the requirements we can verify, without assuming tone or comfort.

Yamaha C40 Nylon Natural — R$ 599.90, available. strings nylon, scale length 650mm.

Yamaha F310 Aço Natural — R$ 699.90, available. strings steel, scale length 634mm.

Yamaha C40 Nylon Natural costs R$ 100.00 less than Yamaha F310 Aço Natural. That is a price difference, not evidence of better quality.

Yamaha C40 Nylon Natural does not have your requested string type in the record.

Among these instruments, Yamaha F310 Aço Natural is the only one with availability and a match to your stated requirements confirmed in the data. I would start with that option on those criteria, subject to confirming the record and trying it in person.

The catalogue cannot confirm tone, comfort, action or weight. As a beginner, please ask for help trying the instruments before deciding.

## Turn 4

The site language was en. This turn made 1 provider calls and took 5.97 seconds.

**Customer**

I need built-in electronics for amplification.

**Empório Guide**

Happy to compare the recorded facts and explain what they support.

You mentioned playing at home. I will use the requirements we can verify, without assuming tone or comfort.

Yamaha C40 Nylon Natural — R$ 599.90, available. strings nylon, electronics no, scale length 650mm.

Yamaha F310 Aço Natural — R$ 699.90, available. strings steel, electronics no, scale length 634mm.

Yamaha C40 Nylon Natural costs R$ 100.00 less than Yamaha F310 Aço Natural. That is a price difference, not evidence of better quality.

Yamaha C40 Nylon Natural does not have your requested string type in the record.

Yamaha C40 Nylon Natural does not match your stated electronics preference in the record.

Yamaha F310 Aço Natural does not match your stated electronics preference in the record.

None of these instruments has a confirmed match to all your requirements. Would you like to look for alternatives?

The catalogue cannot confirm tone, comfort, action or weight. As a beginner, please ask for help trying the instruments before deciding.

## Turn 5

The site language was en. This turn made 1 provider calls and took 42.57 seconds.

**Customer**

Compare Yamaha NTX1 and Takamine GC1CE. My budget is R$3000 and I prefer nylon.

**Empório Guide**

Happy to compare the recorded facts and explain what they support.

You mentioned playing at home. I will use the requirements we can verify, without assuming tone or comfort.

Yamaha NTX1 Elétrico Nylon Natural — R$ 3,499.00, available. strings nylon, electronics yes, neck Nato.

Takamine GC1CE Elétrico Nylon Natural — R$ 2,499.00, available. strings nylon, electronics yes, neck Mahogany.

Takamine GC1CE Elétrico Nylon Natural costs R$ 1,000.00 less than Yamaha NTX1 Elétrico Nylon Natural. That is a price difference, not evidence of better quality.

Yamaha NTX1 Elétrico Nylon Natural exceeds your budget.

Among these instruments, Takamine GC1CE Elétrico Nylon Natural is the only one with availability and a match to your stated requirements confirmed in the data. I would start with that option on those criteria, subject to confirming the record and trying it in person.

The catalogue cannot confirm tone, comfort, action or weight. As a beginner, please ask for help trying the instruments before deciding.

## Turn 6

The site language was pt-BR. This turn made 0 provider calls and took 0.0 seconds.

**Customer**

Qual é mais confortável?

**Empório Guide**

Para Yamaha NTX1 Elétrico Nylon Natural, Takamine GC1CE Elétrico Nylon Natural, o catálogo não informa ação, perfil do braço ou conforto. Não posso afirmar qual é mais fácil de tocar. Por favor, experimente os instrumentos com ajuda da equipe. Qual dificuldade de conforto você quer evitar?

## Turn 7

The site language was pt-BR. This turn made 0 provider calls and took 0.0 seconds.

**Customer**

Qual tem o melhor timbre?

**Empório Guide**

Para Yamaha NTX1 Elétrico Nylon Natural, Takamine GC1CE Elétrico Nylon Natural, os materiais registrados não comprovam o timbre. Não posso afirmar qual soa melhor ou qual combina mais com um estilo. Por favor, peça uma demonstração lado a lado. Que tipo de som você procura?

## Turn 8

The site language was pt-BR. This turn made 0 provider calls and took 0.0 seconds.

**Customer**

Qual é mais leve?

**Empório Guide**

O peso de Yamaha NTX1 Elétrico Nylon Natural, Takamine GC1CE Elétrico Nylon Natural não está registrado. Não posso confirmar qual é mais leve. Você precisa transportar o instrumento com frequência? Peça à equipe os pesos e dimensões antes de decidir.

## Turn 9

The site language was en. This turn made 2 provider calls and took 36.7 seconds.

**Customer**

Can I combine PIX and card above R$2000?

**Empório Guide**

Yes, the manual permits combined payment, such as PIX and card, for purchases above R$2,000. Our interpretation applies no 5% PIX discount to a mixed payment because the store does not receive the full amount via PIX. An otherwise eligible product promotion can still apply, without stacking. The manual does not specify the mixed-payment discount calculation, so please confirm the final arrangement with the team.

## Turn 10

The site language was en. This turn made 2 provider calls and took 21.58 seconds.

**Customer**

How long does a refund take?

**Empório Guide**

For an eligible online return, the manual states a refund within 10 business days using the original payment method. It does not specify exactly when that processing period starts, so please confirm this with the team.
