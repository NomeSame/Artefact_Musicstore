"""Record honest preview transcripts from actual HTTP requests to the running app."""
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
SCENARIOS=[
    ("01_catalogue_preview",[
        ("Show acoustic guitars under R$1000",{}),
        ("What does this instrument cost with PIX?",{"category_id":5,"selected_product_id":81}),
    ]),
    ("02_returns_preview",[("What are the return rules?",{})]),
    ("03_order_scope_preview",[
        ("Where is order 1?",{}),
        ("What are the store opening hours?",{}),
    ]),
]
def main():
    # Preview diagnostics must never overwrite or expand the final live examples.
    output=ROOT/".runtime"/"preview-examples"
    output.mkdir(parents=True,exist_ok=True)
    for name,turns in SCENARIOS:
        with httpx.Client(base_url="http://127.0.0.1:8765",trust_env=False,timeout=30) as client:
            client.get("/api/bootstrap").raise_for_status()
            for message,context in turns:
                response=client.post("/api/chat",json={"message":message,"context":context})
                response.raise_for_status()
                assert response.json()["mode"]=="preview"
            transcript=client.get("/api/chat/export")
            transcript.raise_for_status()
            prefix=("This example was recorded by scripts/record_examples.py against the running local app. "
                    "It demonstrates the deterministic tool preview and is not evidence of a real LLM evaluation.\n\n")
            (output/(name+".md")).write_text(prefix+transcript.text,encoding="utf-8")
    print("Recorded three real preview conversations, clearly labelled without LLM claims.")
if __name__=="__main__":
    main()
