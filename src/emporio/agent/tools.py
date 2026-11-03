"""A single validated tool boundary shared by the browser, agent and MCP."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from emporio.data.catalog import Catalog
from emporio.data.policies import Policies

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")
class SearchInput(Input):
    query: str = Field(default="", max_length=150)
    category_id: int | None = Field(default=None, ge=1, le=9)
    max_price: float | None = Field(default=None, ge=0, le=10000000, allow_inf_nan=False)
    available_only: bool = True
    payment: str = Field(default="unspecified", pattern="^(unspecified|pix|card|debit|boleto)$")
class ProductInput(Input):
    focus: Literal["overview", "specifications", "sound", "availability", "price"] = "price"
    product_id: int = Field(ge=1)
    payment: str = Field(default="unspecified", pattern="^(unspecified|pix|card|debit|boleto)$")
class PolicyInput(Input):
    topic: str = Field(min_length=1, max_length=150)
class OrderInput(Input):
    order_id: int = Field(ge=1)
class NavigationInput(Input):
    category_id: int | None = Field(default=None, ge=1, le=9)
    product_id: int | None = Field(default=None, ge=1)

DEFINITIONS = {
    "search_products": (SearchInput, "Find instruments by name, category, maximum BRL price and availability. Categories 1 electric guitars, 2 bass, 3 drums, 4 keys/pianos, 5 acoustic guitars, 6 woodwinds, 7 brass, 8 orchestral strings, 9 ukuleles. Use current category only for implicit references. Never invent product IDs."),
    "get_product": (ProductInput, "Get verified details for an existing product. Choose focus overview for its description, specifications for build/materials, sound for recorded sound/electronics facts, availability for stock, or price for a quote. PIX applies only when the store receives full immediate PIX payment. Never stack discounts."),
    "lookup_policy": (PolicyInput, "Retrieve store policies with source PDF pages. Topics store, payments, returns, delivery, promotions, warranty, privacy. Use for factual policy answers."),
    "get_order": (OrderInput, "Read a specific order only after the customer has used the order number and email verification dialog. If not verified, request that dialog. Does not perform refunds, purchases or shipping updates."),
    "navigate_catalog": (NavigationInput, "Open a category or select an existing product in the visible catalogue. A selected product must belong to the requested category. This changes navigation only."),
}

OUTPUT_FIELDS = {
    "search_products": {"found": {"type": "boolean"}, "products": {"type": "array", "items": {"type": "object"}},
                        "count": {"type": "integer"}, "snapshot": {"type": "boolean"}, "filters": {"type": "object"}},
    "get_product": {"found": {"type": "boolean"}, "product": {"type": ["object", "null"]},
                    "focus": {"enum": ["overview", "specifications", "sound", "availability", "price"]}},
    "lookup_policy": {"found": {"type": "boolean"}, "topic": {"type": "string"},
                      "summary": {"type": "string"}, "sources": {"type": "array", "items": {
                          "type": "object", "required": ["document", "page", "text"],
                          "properties": {"document": {"type": "string"}, "page": {"type": "integer"},
                                         "text": {"type": "string"}}}}},
    "get_order": {"found": {"type": "boolean"}, "order": {"type": ["object", "null"]},
                  "snapshot": {"type": "boolean"}},
    "navigate_catalog": {"action": {"type": "object", "properties": {
        "category_id": {"type": ["integer", "null"]}, "product_id": {"type": ["integer", "null"]}}}},
}
def output_schema(name):
    return {"type": "object", "properties": {
        "error": {"type": "string"}, "message": {"type": "string"}, **OUTPUT_FIELDS[name]}}

class Tools:
    def __init__(self, catalog: Catalog, policies: Policies):
        self.catalog, self.policies = catalog, policies
    def catalog_schema(self):
        return [{"name": name, "description": desc, "input_schema": model.model_json_schema(),
                 "output_schema": output_schema(name),
                 "side_effects": "Browser navigation only." if name == "navigate_catalog" else "Read only.",
                 "access": "Verified order in the current browser session." if name == "get_order" else "Public catalogue or manual."}
                for name, (model, desc) in DEFINITIONS.items()]
    def model_schema(self):
        return [{"type": "function", "function": {"name": d["name"],
                "description": d["description"], "parameters": d["input_schema"]}}
                for d in self.catalog_schema()]
    def execute(self, name, arguments, verified_order=None):
        if name not in DEFINITIONS:
            return {"error": "unknown_tool", "message": "This tool is not available."}
        try:
            args = DEFINITIONS[name][0].model_validate(arguments).model_dump()
        except (ValidationError, TypeError):
            return {"error": "invalid_arguments", "message": "Arguments do not match the documented tool schema."}
        if name == "search_products":
            products = self.catalog.search(**args, limit=12)
            return {"found": bool(products), "products": products,
                    "count": len(products), "snapshot": True, "filters": args}
        if name == "get_product":
            focus = args.pop("focus")
            product = self.catalog.product(**args)
            return {"found": bool(product), "product": product, "focus": focus}
        if name == "lookup_policy":
            return self.policies.lookup(**args)
        if name == "get_order":
            if args["order_id"] != verified_order:
                return {"error": "verification_required", "message": "Use the order lookup dialog with order number and matching email first."}
            return {"found": True, "order": self.catalog.order(args["order_id"]), "snapshot": True}
        if name == "navigate_catalog":
            product = self.catalog.product(args["product_id"]) if args["product_id"] else None
            if args["product_id"] and not product:
                return {"error": "not_found", "message": "Unknown product."}
            if product and args["category_id"] and product["category_id"] != args["category_id"]:
                return {"error": "category_mismatch", "message": "That product is in a different category."}
            return {"action": {"category_id": product["category_id"] if product else args["category_id"],
                               "product_id": args["product_id"]}}
        return {"error": "unknown_tool"}
