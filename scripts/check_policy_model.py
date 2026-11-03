"""Opt-in live policy evaluation. Writes actual requests, responses and assertions locally."""
import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from emporio.agent.engine import Agent
from emporio.integrations.provider import Provider
from emporio.session.state import Session
from emporio.web.app import create_app, ROOT

CASES = [
    (81, "en", "Can I pay for this instrument in 12 credit card installments without interest, and what is the minimum installment?", ["12", "R$100"], ["5%", "shipping"]),
    (135, "en", "For an order above R$2000, can I combine PIX and credit card?", ["above R$2,000", "no 5%", "promotion"], ["R$80", "shipping"]),
    (81, "en", "If my bank offers PIX in installments and the store gets the full amount immediately, do I get the PIX discount?", ["5%", "full amount", "bank"], ["R$80", "shipping"]),
    (131, "en", "For an online return, how long does the refund take and which payment method is used?", ["10 business days", "original payment"], ["90 days", "R$35"]),
    (142, "en", "Does the warranty cover damage from a fall or unauthorized repairs?", ["falls", "unauthorized"], ["R$35", "90 days"]),
    (139, "en", "Can delivery of a large instrument require a special individual shipping quote?", ["individual quote", "postcode"], ["R$35", "12 interest"]),
    (121, "en", "What PIX discount is offered and can I stack it with a promotion?", ["5%", "do not stack"], ["R$80", "shipping"]),
    (142, "en", "What are your opening hours on Saturday and are you closed on Sundays?", ["13:00", "Sundays"], ["PIX", "warranty"]),
    (81, "pt-BR", "Posso combinar parte em PIX e parte no cartão em uma compra acima de R$2.000?", ["5%", "não se aplica", "promoção"], ["R$80", "frete"]),
    (131, "pt-BR", "Em quantos dias recebo o reembolso e por qual forma de pagamento?", ["10 dias úteis", "original"], ["90 dias", "PIX"]),
    (139, "pt-BR", "Uma bateria grande pode precisar de frete especial com cotação individual?", ["cotação individual", "CEP"], ["R$35", "garantia"]),
    (81, "pt-BR", "O PIX parcelado pelo banco tem desconto se a loja recebe o valor integral imediatamente?", ["5%", "integral", "banco"], ["R$80", "frete"]),
]

async def run(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    app = create_app(ROOT, out / "catalogue.sqlite3")
    requests = []
    class Recorder(Provider):
        async def complete(self, model, messages, tools):
            record = {"model": model, "messages": json.loads(json.dumps(messages))}
            requests.append(record)
            result = await super().complete(model, messages, tools)
            record["response"] = result
            return result
    agent = Agent(app.state.tools, lambda *a: Recorder(*a))
    # One conversation deliberately changes instrument and language between turns.
    session = Session(base_url=args.base_url, model=args.model)
    results = []
    for index, (product, language, question, required, excluded) in enumerate(CASES):
        session.language = language
        started = time.monotonic()
        try:
            reply = await agent.reply(session, question, {"selected_product_id": product})
            answer = reply["answer"]
            checks = {"required": all(s in answer for s in required),
                      "excluded": not any(s in answer for s in excluded),
                      "no_unsolicited_cards": not reply["products"],
                      "policy_consulted": any(t["name"] == "lookup_policy" for t in reply["trace"])}
            record = {"case": index + 1, "product_id": product, "language": language,
                      "question": question, "reply": reply, "checks": checks,
                      "passed": all(checks.values()), "seconds": round(time.monotonic()-started, 2)}
        except Exception as error:
            record = {"case": index+1, "question": question, "passed": False, "error": str(error)}
        results.append(record)
        (out / "results.json").write_text(json.dumps({"model": args.model, "base_url": args.base_url,
            "utc": datetime.now(timezone.utc).isoformat(), "cases": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "model-requests.json").write_text(json.dumps(requests, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: record[k] for k in ("case", "passed", "question")}, ensure_ascii=True), flush=True)
        if record.get("error"):
            break  # Never pile new inference onto a timed-out request.
    print(f"Passed {sum(r['passed'] for r in results)}/{len(results)} executed cases", flush=True)
    return 0 if len(results) == len(CASES) and all(r["passed"] for r in results) else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--model", default="Bonsai27B")
    parser.add_argument("--output", default=str(ROOT / ".runtime/bonsai-policy-evaluation"))
    raise SystemExit(asyncio.run(run(parser.parse_args())))
