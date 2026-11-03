# Order verification and session scope

This is an actual conversation from the final functional acceptance on 3 November 2026. The configured local model was Bonsai27B at `http://127.0.0.1:8080/v1`. The server reported Bonsai-27B-Q1_0.gguf with very high reasoning effort. Its settings were not changed. Questions were prepared for evaluation rather than collected from independent customers.

Each group used its own real application session through FastAPI routes and the live model provider. The model selected tools, while the application validated the request evidence and produced the visible factual replies. Direct application clarifications and API verification events are identified separately. This evaluates the application with the model and does not attribute every correct sentence to free model generation.

This conversation contains 4 chat turns and 3 API events. It made 4 provider calls. All its recorded checks passed. The complete run passed 24 steps across three sessions, including independently calculated CSV price expectations.

The report revision label is `64da508+acceptance-fixes`. It describes a working tree based on the stated commit, not a new commit ID. The exact application hashes, actual replies, checks and model requests are recorded under `.runtime/model-acceptance-verified`. Earlier failed attempts remain in separate runtime folders. The reproducible runner is `scripts/check_model_acceptance.py`. This was functional acceptance, and the separate final injection campaign is still open.

## O01

The site language was en, with payment setting unspecified. This turn made 1 provider calls and took 13.22 seconds.

**Customer**

What is the status of order 1?

**Empório Guide**

Use the order lookup dialog with order number and matching email first.

Recorded tools were `get_order`.

## O02

The evaluator submitted order 1 with a deliberately non-matching email through the order lookup route. It returned HTTP 403 and did not verify the session.

## O03

The evaluator submitted order 1 with the matching email from the supplied fictional customer data through the order lookup route. It returned HTTP 200 and verified that order in this session. The email is omitted here.

## O04

The site language was en, with payment setting unspecified. This turn made 1 provider calls and took 8.45 seconds.

**Customer**

What is the status and tracking reference of order 1?

**Empório Guide**

Order #1 is recorded as delivered in the supplied snapshot. Tracking reference: BRAB1234567BR.

Recorded tools were `get_order`.

## O05

The site language was en, with payment setting unspecified. This turn made 1 provider calls and took 17.25 seconds.

**Customer**

What is the status and tracking reference of order 2?

**Empório Guide**

Use the order lookup dialog with order number and matching email first.

Recorded tools were `get_order`.

## O06

The evaluator reset this conversation through the application route. It returned HTTP 200. The next chat request tests the cleared verification state.

## O07

The site language was en, with payment setting unspecified. This turn made 1 provider calls and took 2.53 seconds.

**Customer**

What is the status of order 1?

**Empório Guide**

Use the order lookup dialog with order number and matching email first.

Recorded tools were `get_order`.
