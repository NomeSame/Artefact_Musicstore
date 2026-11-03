"""Loopback-only web API and static UI."""
import asyncio
import time
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict
from emporio.data.catalog import Catalog
from emporio.data.policies import Policies
from emporio.agent.tools import Tools, SearchInput
from emporio.agent.engine import Agent
from emporio.integrations.provider import Provider, ProviderError, validate_base_url
from emporio.session.state import Sessions
from emporio.domain.language import product_for_language, POLICIES_PT

ROOT = Path(__file__).resolve().parents[3]
STATIC = Path(__file__).parent / "static"

class ConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_url: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=200)
    api_key: str | None = Field(default=None, max_length=4096, repr=False)
    no_key: bool = False

class Context(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = Field(default=None, ge=1, le=9)
    selected_product_id: int | None = Field(default=None, ge=1)
    max_price: float | None = Field(default=None, ge=0, le=10000000, allow_inf_nan=False)
    payment: Literal["unspecified", "pix", "card", "debit", "boleto"] = "unspecified"
    visible_product_ids: list[int] = Field(default_factory=list, max_length=100)

class LanguageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["en", "pt-BR"]

class ChatInput(BaseModel):
    language: Literal["en", "pt-BR"] | None = None
    message: str = Field(min_length=1, max_length=3000)
    context: Context = Field(default_factory=Context)

class NavigationConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str = Field(min_length=20, max_length=100)

class OrderVerification(BaseModel):
    order_id: int = Field(ge=1)
    email: str = Field(min_length=3, max_length=254)

def create_app(root=ROOT, db_path=None, provider_factory=Provider):
    catalog = Catalog(root / "data", db_path or root / ".runtime" / "catalog.sqlite3")
    policies = Policies(root / "data" / "políticas_da_loja.pdf")
    tools, sessions = Tools(catalog, policies), Sessions()
    valid_ids = {p["product_id"] for p in catalog.search()}
    agent = Agent(tools, provider_factory)
    app = FastAPI(title="Empório da Música", version="0.1.0")
    app.state.tools, app.state.sessions = tools, sessions
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def local_boundary(request, call_next):
        if request.url.path.startswith("/api"):
            if request.headers.get("sec-fetch-site") == "cross-site":
                return PlainTextResponse("Cross-site requests are not allowed.", status_code=403)
            origin = request.headers.get("origin")
            if origin and origin not in {f"http://{request.headers['host']}", f"https://{request.headers['host']}"}:
                return PlainTextResponse("Origin not allowed.", status_code=403)
            if request.method == "POST":
                try:
                    size = int(request.headers.get("content-length", 0))
                except ValueError:
                    return PlainTextResponse("Invalid request size.", status_code=400)
                if size > 64000 or len(await request.body()) > 64000:
                    return PlainTextResponse("Request too large.", status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def session_for(request: Request, response: Response):
        try:
            token, session = sessions.get(request.cookies.get("emporio_session"))
        except ValueError as error:
            raise HTTPException(429, str(error)) from None
        if token != request.cookies.get("emporio_session"):
            response.set_cookie("emporio_session", token, httponly=True, samesite="strict", max_age=7200)
        return session

    def public_config(session):
        return {"base_url": session.base_url, "model": session.model,
                "has_key": bool(session.api_key),
                "mode": "model" if session.base_url and session.model else "preview"}

    @app.get("/api/bootstrap")
    def bootstrap(session=Depends(session_for)):
        return {"categories": catalog.categories(), "product_count": len(catalog.search()),
                "config": public_config(session), "language": session.language, "snapshot": True, "verified_order": session.verified_order}

    @app.post("/api/language")
    async def set_language(body: LanguageInput, session=Depends(session_for)):
        async with session.lock:
            session.language = body.language
            session.pending_navigation.clear()
        return {"language": session.language}

    @app.get("/api/products")
    def products(query: str = "", category_id: int | None = None, max_price: float | None = None,
                 available_only: bool = False, payment: str = "unspecified", sort: str = "recommended",
                 language: Literal["en", "pt-BR"] = "en"):
        try:
            args = SearchInput(query=query, category_id=category_id, max_price=max_price,
                               available_only=available_only, payment=payment).model_dump()
            result = catalog.search(**args, sort=sort)
            return {"products": [product_for_language(p, language) for p in result], "count": len(result)}
        except ValueError:
            raise HTTPException(422, "Invalid catalogue filters.") from None

    @app.get("/api/products/{product_id}")
    def product_details(product_id: int, payment: str = "unspecified", language: Literal["en", "pt-BR"] = "en"):
        try:
            if payment not in {"unspecified", "pix", "card", "debit", "boleto"}:
                raise ValueError
            product = catalog.product(product_id, payment=payment)
        except ValueError:
            raise HTTPException(422, "Invalid product quote settings.") from None
        if not product:
            raise HTTPException(404, "This instrument is not in the catalogue.")
        buying_policies = []
        for topic in ("delivery", "returns", "warranty"):
            policy = policies.lookup(topic)
            buying_policies.append({"topic": topic, "summary": POLICIES_PT[topic] if language == "pt-BR" else policy["summary"],
                "sources": [{"document": source["document"], "page": source["page"]}
                            for source in policy["sources"]]})
        return {"product": product_for_language(product, language), "policies": buying_policies}

    @app.get("/products/{product_id}")
    def product_page(product_id: int):
        if product_id not in valid_ids:
            raise HTTPException(404, "This instrument is not in the catalogue.")
        return FileResponse(STATIC / "index.html")

    @app.get("/api/manual")
    def manual():
        return FileResponse(root / "data" / "políticas_da_loja.pdf", media_type="application/pdf")

    @app.get("/api/tools")
    def tool_catalog():
        return {"tools": tools.catalog_schema()}

    @app.post("/api/config")
    async def configure(body: ConfigInput, session=Depends(session_for)):
        async with session.lock:
            old_url = session.base_url
            if body.base_url:
                try:
                    session.base_url = validate_base_url(body.base_url)
                except ValueError as error:
                    raise HTTPException(422, str(error)) from None
            else:
                session.base_url = ""
            session.model = body.model.strip()
            if body.no_key or (session.base_url != old_url and body.api_key is None):
                session.api_key = ""
            elif body.api_key is not None:
                session.api_key = body.api_key.strip()
            session.history.clear()
            session.pending_navigation.clear()
            return public_config(session)

    @app.post("/api/models")
    async def models(session=Depends(session_for)):
        if not session.base_url:
            raise HTTPException(422, "Set an API base URL first.")
        try:
            return {"models": await provider_factory(session.base_url, session.api_key).models(),
                    "note": "Model listing does not verify tool-calling support."}
        except ProviderError as error:
            raise HTTPException(502, str(error)) from None

    @app.post("/api/chat")
    async def chat(body: ChatInput, session=Depends(session_for)):
        if not body.message.strip():
            raise HTTPException(422, "Please enter a message.")
        context = body.context.model_dump()
        product = catalog.product(context["selected_product_id"]) if context["selected_product_id"] else None
        if context["selected_product_id"] and not product:
            raise HTTPException(422, "Selected product does not exist.")
        if product and context["category_id"] and product["category_id"] != context["category_id"]:
            raise HTTPException(422, "Selection does not match the category.")
        context["visible_product_ids"] = [p for p in context["visible_product_ids"] if p in valid_ids]
        try:
            async with session.lock:
                if body.language is not None:
                    session.language = body.language
                return await asyncio.wait_for(agent.reply(session, body.message.strip(), context), timeout=120)
        except (ProviderError, asyncio.TimeoutError) as error:
            raise HTTPException(502, str(error) or "The request timed out. Please try again.") from None

    @app.post("/api/navigation/confirm")
    async def confirm_navigation(body: NavigationConfirmation, session=Depends(session_for)):
        # The model cannot supply confirmation. Only this browser session can consume
        # its short-lived, exact-target proposal. Client-supplied target overrides fail.
        async with session.lock:
            proposal = session.pending_navigation.pop(body.proposal_id, None)
            if not proposal or proposal["expires"] <= time.monotonic():
                raise HTTPException(409, "This suggestion expired. Ask for a new one.")
            result = tools.execute("navigate_catalog", proposal["target"])
            if "navigation_proposal" not in result:
                raise HTTPException(409, "This catalogue suggestion is no longer available.")
            return {"action": result["navigation_proposal"]}

    @app.post("/api/orders/verify")
    async def verify_order(body: OrderVerification, session=Depends(session_for)):
        async with session.lock:
            session.verified_order = None
            if not catalog.verify_order(body.order_id, body.email):
                raise HTTPException(403, "Order number and email do not match the supplied snapshot.")
            session.verified_order = body.order_id
            return {"order": catalog.order(body.order_id),
                    "note": "Prototype knowledge check, not production authentication."}

    @app.post("/api/chat/reset")
    async def reset(session=Depends(session_for)):
        async with session.lock:
            session.history.clear()
            session.transcript.clear()
            session.pending_navigation.clear()
            session.verified_order = None
        return {"ok": True}

    @app.get("/api/chat/export")
    def export(session=Depends(session_for)):
        lines = ["# Empório da Música conversation", "",
                 "Recorded from this local prototype. Preview mode is deterministic and is not an LLM evaluation.", ""]
        for turn in session.transcript:
            lines.extend(["## Customer", "", turn["user"], "", "## Assistant", "", turn["answer"], "",
                          "Mode " + turn["mode"] + (", model " + turn["model"] if turn["model"] else ""),
                          "", "Tools " + (", ".join(turn["tools"]) or "none"), ""])
        return PlainTextResponse("\n".join(lines), media_type="text/markdown",
                                 headers={"Content-Disposition": 'attachment; filename="conversation.md"'})

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    return app
