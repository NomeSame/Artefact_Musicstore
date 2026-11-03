"""Load the supplied snapshot into SQLite and expose bounded read operations."""
import csv
import json
import sqlite3
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from emporio.domain.pricing import cents, quote
from emporio.data.corrections import CORRECTIONS, CONFLICTS, catalogue_warning, corrected_products

CATEGORY_NAMES = {
    1: "Electric guitars", 2: "Bass guitars", 3: "Drums & percussion",
    4: "Keys & pianos", 5: "Acoustic guitars", 6: "Woodwinds",
    7: "Brass", 8: "Orchestral strings", 9: "Ukuleles",
}
def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(text)).lower()
                   if not unicodedata.combining(c))

class Catalog:
    def __init__(self, data_dir: Path, db_path: Path):
        self.data_dir, self.db_path = data_dir, db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.import_snapshot()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.create_function("norm", 1, normalize)
        try:
            yield conn
        finally:
            conn.close()

    def rows(self, table):
        path = self.data_dir / f"desafio_tecnico_ai_eng - {table}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    def import_snapshot(self):
        # Rebuild the derived snapshot. Original source files are untouched.
        with self.connect() as conn, conn:
            for table in ("product_conflicts", "order_items", "orders", "customers", "promotions", "products", "categories"):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.executescript("""
                CREATE TABLE categories(category_id INTEGER PRIMARY KEY,name TEXT,description TEXT);
                CREATE TABLE products(
                    product_id INTEGER PRIMARY KEY,price_cents INTEGER NOT NULL CHECK(price_cents>=0),
                    name TEXT,category_id INTEGER REFERENCES categories,description TEXT,
                    stock_quantity INTEGER CHECK(stock_quantity>=0),status TEXT,specs TEXT,created_at TEXT);
                CREATE TABLE promotions(promotion_id INTEGER PRIMARY KEY,
                    product_id INTEGER REFERENCES products,discount_percent INTEGER CHECK(discount_percent BETWEEN 0 AND 100),
                    description TEXT,is_active INTEGER CHECK(is_active IN (0,1)));
                CREATE TABLE product_conflicts(product_id INTEGER PRIMARY KEY REFERENCES products,
                    unconfirmed_fields TEXT NOT NULL);
                CREATE TABLE customers(customer_id INTEGER PRIMARY KEY,name TEXT,phone TEXT,email TEXT,city TEXT);
                CREATE TABLE orders(order_id INTEGER PRIMARY KEY,customer_id INTEGER REFERENCES customers,
                    order_date TEXT,status TEXT,total_cents INTEGER,payment_method TEXT,
                    tracking_code TEXT,estimated_delivery TEXT,notes TEXT);
                CREATE TABLE order_items(order_id INTEGER REFERENCES orders,quantity INTEGER CHECK(quantity>0),
                    product_id INTEGER REFERENCES products);
            """)
            for row in self.rows("categories"):
                conn.execute("INSERT INTO categories VALUES(?,?,?)", tuple(row.values()))
            for row in corrected_products(self.rows("products")):
                json.loads(row["specs"])
                conn.execute("INSERT INTO products VALUES(?,?,?,?,?,?,?,?,?)", (
                    row["product_id"], cents(row["price_brl"]), row["name"], row["category_id"],
                    row["description"], row["stock_quantity"], row["status"], row["specs"], row["created_at"]))
            for product_id, conflict in CONFLICTS.items():
                conn.execute("INSERT INTO product_conflicts VALUES(?,?)", (product_id, json.dumps(conflict["fields"])))
            for row in self.rows("promotions"):
                conn.execute("INSERT INTO promotions VALUES(?,?,?,?,?)", tuple(row.values()))
            for row in self.rows("customers"):
                conn.execute("INSERT INTO customers VALUES(?,?,?,?,?)", tuple(row.values()))
            for row in self.rows("orders"):
                conn.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?)", (
                    row["order_id"], row["customer_id"], row["order_date"], row["status"], cents(row["total_brl"]),
                    row["payment_method"], row["tracking_code"], row["estimated_delivery"], row["notes"]))
            for row in self.rows("order_items"):
                conn.execute("INSERT INTO order_items VALUES(?,?,?)", tuple(row.values()))

    def categories(self):
        with self.connect() as conn:
            return [{**dict(r), "label": CATEGORY_NAMES[r["category_id"]]} for r in conn.execute(
                "SELECT c.*, COUNT(p.product_id) AS count FROM categories c "
                "LEFT JOIN products p USING(category_id) GROUP BY c.category_id ORDER BY c.category_id")]

    def search(self, query="", category_id=None, max_price=None, available_only=False,
               payment="unspecified", sort="recommended", limit=100):
        terms, params = [], []
        if category_id is not None:
            terms.append("p.category_id=?")
            params.append(category_id)
        if available_only:
            terms.append("p.status='active' AND p.stock_quantity>0")
        for token in normalize(query).split()[:8]:
            terms.append("instr(norm(p.name || ' ' || p.description),?)>0")
            params.append(token)
        sql = ("SELECT p.*, pc.unconfirmed_fields, COALESCE((SELECT MAX(discount_percent) FROM promotions pr "
               "WHERE pr.product_id=p.product_id AND pr.is_active=1),0) AS promotion_percent "
               "FROM products p LEFT JOIN product_conflicts pc USING(product_id)" + (" WHERE " + " AND ".join(terms) if terms else ""))
        with self.connect() as conn:
            rows = [self.product_data(dict(r), payment) for r in conn.execute(sql, params)]
        if max_price is not None:
            rows = [r for r in rows if r["price_cents"] <= cents(max_price)]
        if sort == "price_asc":
            rows.sort(key=lambda r: (r["price_cents"], r["product_id"]))
        elif sort == "price_desc":
            rows.sort(key=lambda r: (-r["price_cents"], r["product_id"]))
        else:
            rows.sort(key=lambda r: (not r["available"], -r["promotion_percent"], r["product_id"]))
        return rows[:max(1, min(limit, 100))]

    def product_data(self, row, payment):
        row["specs"] = json.loads(row["specs"])
        row["unconfirmed_fields"] = json.loads(row["unconfirmed_fields"] or "[]")
        row["catalogue_conflict"] = bool(row["unconfirmed_fields"])
        row["recommendation_eligible"] = not row["catalogue_conflict"]
        correction = CORRECTIONS.get(row["product_id"])
        if correction:
            row["description_source_product_id"] = correction["description_source_product_id"]
        warning = catalogue_warning(row["product_id"])
        if warning:
            row["catalogue_warning"] = warning
        row["available"] = row["status"] == "active" and row["stock_quantity"] > 0
        row["category_label"] = CATEGORY_NAMES[row["category_id"]]
        row.update(quote(row.pop("price_cents"), row["promotion_percent"], payment))
        return row

    def product(self, product_id, payment="unspecified"):
        # IDs are validated independently of any model-generated category.
        return next((r for r in self.search(payment=payment) if r["product_id"] == product_id), None)

    def verify_order(self, order_id, email):
        with self.connect() as conn:
            return conn.execute("SELECT o.order_id FROM orders o JOIN customers c USING(customer_id) "
                                "WHERE o.order_id=? AND lower(c.email)=lower(?)",
                                (order_id, email.strip())).fetchone() is not None

    def order(self, order_id):
        with self.connect() as conn:
            row = conn.execute("SELECT order_id,order_date,status,total_cents,payment_method,"
                               "tracking_code,estimated_delivery FROM orders WHERE order_id=?",
                               (order_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["items"] = [dict(r) for r in conn.execute(
                "SELECT i.quantity,p.product_id,p.name FROM order_items i "
                "JOIN products p USING(product_id) WHERE order_id=?", (order_id,))]
            return result
