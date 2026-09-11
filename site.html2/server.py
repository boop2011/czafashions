from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import uuid

try:
    import psycopg2  # type: ignore[import-not-found]
except Exception:
    psycopg2 = None

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "name": "Sculpt Knit Set",
        "category": "women",
        "price": 129,
        "subtitle": "Soft wool blend",
        "badge": "New",
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 2,
        "name": "Tailored Wool Coat",
        "category": "women",
        "price": 240,
        "subtitle": "Structured warmth",
        "badge": "Trending",
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 3,
        "name": "Monochrome Hoodie",
        "category": "men",
        "price": 98,
        "subtitle": "Premium cotton",
        "badge": "Bestseller",
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 4,
        "name": "Layered Utility Shirt",
        "category": "men",
        "price": 118,
        "subtitle": "Relaxed fit",
        "badge": "Limited",
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 5,
        "name": "Aster Leather Tote",
        "category": "accessories",
        "price": 142,
        "subtitle": "Italian leather",
        "badge": "Top pick",
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 6,
        "name": "Hayden Sunglasses",
        "category": "accessories",
        "price": 74,
        "subtitle": "UV protection",
        "badge": "Hot",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 7,
        "name": "Luna Overshirt",
        "category": "women",
        "price": 136,
        "subtitle": "Lightweight layer",
        "badge": "New",
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
    },
    {
        "id": 8,
        "name": "Noir Striped Tee",
        "category": "men",
        "price": 68,
        "subtitle": "Essential staple",
        "badge": "Sale",
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
    },
]

MAKYPAY_BASE64_HEADER = os.getenv(
    "MAKYPAY_BASE64_HEADER",
    "bWFreV92MV9wdWJfVlhHdE5CN1ZETkE4dXJzVlYzVGY6bWFreV92MV9zZWNfWlVsN1JwWjRTRXRXNUZQVWszOHFHUXd3U0E2T1BqUTY=",
)
MAKYPAY_SECRET_KEY = os.getenv("MAKYPAY_SECRET_KEY", "maky_v1_sec_ZUl7RpZ4SEtW5FPUk38qGQwwSA6OPjQ6")
MAKYPAY_API_BASE_URL = os.getenv("MAKYPAY_API_BASE_URL", "https://wire-api.makylegacy.com/api/v1")
MAKYPAY_SUCCESS_URL = os.getenv("MAKYPAY_SUCCESS_URL", "https://czafashions.com/shop")
MAKYPAY_CANCEL_URL = os.getenv("MAKYPAY_CANCEL_URL", "https://czafashions.com/shop")
MAKYPAY_WEBHOOK_SECRET = os.getenv("MAKYPAY_WEBHOOK_SECRET", "")


def ensure_json(path: Path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_phone_number(phone_number):
    if not phone_number:
        return ""
    value = str(phone_number).strip().replace(" ", "")
    if value.startswith("+"):
        return value[1:]
    return value


def is_makypay_configured():
    return bool(MAKYPAY_BASE64_HEADER and MAKYPAY_BASE64_HEADER != "YOUR_BASE64_HEADER")


def get_database_url():
    return os.getenv("DATABASE_URL", "")


def has_database():
    return bool(get_database_url()) and psycopg2 is not None


def get_db_connection():
    if not has_database():
        return None

    try:
        return psycopg2.connect(get_database_url(), sslmode="require")
    except Exception:
        return None


def ensure_database():
    if not has_database():
        return False

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id bigint PRIMARY KEY,
                    payload jsonb NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id bigint PRIMARY KEY,
                    payload jsonb NOT NULL
                )
                """
            )

            cur.execute("SELECT COUNT(*) FROM products")
            if cur.fetchone()[0] == 0:
                for product in DEFAULT_PRODUCTS:
                    cur.execute(
                        "INSERT INTO products (id, payload) VALUES (%s, %s)",
                        (product["id"], json.dumps(product)),
                    )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def load_products_from_db():
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT payload FROM products ORDER BY id ASC")
            rows = cur.fetchall()
        return [json.loads(row[0]) for row in rows]
    except Exception:
        return None
    finally:
        conn.close()


def load_orders_from_db():
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT payload FROM orders ORDER BY id DESC")
            rows = cur.fetchall()
        return [json.loads(row[0]) for row in rows]
    except Exception:
        return None
    finally:
        conn.close()


def save_products_to_db(products):
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM products")
            for product in products:
                cur.execute(
                    "INSERT INTO products (id, payload) VALUES (%s, %s)",
                    (product.get("id"), json.dumps(product)),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def save_orders_to_db(orders):
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orders")
            for order in orders:
                cur.execute(
                    "INSERT INTO orders (id, payload) VALUES (%s, %s)",
                    (order.get("id"), json.dumps(order)),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def load_products_from_file():
    return ensure_json(DATA_DIR / "products.json", DEFAULT_PRODUCTS)


def load_orders_from_file():
    return ensure_json(DATA_DIR / "orders.json", [])


def save_products_to_file(products):
    write_json(DATA_DIR / "products.json", products)


def save_orders_to_file(orders):
    write_json(DATA_DIR / "orders.json", orders)


def get_products():
    if has_database():
        ensure_database()
        products = load_products_from_db()
        if products is not None:
            return products

    return load_products_from_file()


def get_orders():
    if has_database():
        ensure_database()
        orders = load_orders_from_db()
        if orders is not None:
            return orders

    return load_orders_from_file()


def save_products(products):
    if has_database():
        if save_products_to_db(products):
            save_products_to_file(products)
            return True

    save_products_to_file(products)
    return True


def save_orders(orders):
    if has_database():
        if save_orders_to_db(orders):
            save_orders_to_file(orders)
            return True

    save_orders_to_file(orders)
    return True


def build_makypay_body(order_payload):
    amount_value = order_payload.get("amount")
    if amount_value in (None, ""):
        amount_value = order_payload.get("total") or 0

    amount = int(float(amount_value))
    reference = str(order_payload.get("reference") or order_payload.get("id") or uuid.uuid4())
    country = str(order_payload.get("country") or order_payload.get("deliveryCountry") or "UG").strip() or "UG"

    form_data = {
        "amount": str(amount),
        "country": country,
        "reference": reference,
        "description": f"Payment for order {order_payload.get('id', reference)}",
        "success_url": MAKYPAY_SUCCESS_URL,
        "cancel_url": MAKYPAY_CANCEL_URL,
    }

    phone_number = normalize_phone_number(order_payload.get("customerPhone") or order_payload.get("phone_number"))
    if phone_number:
        form_data["phone_number"] = phone_number

    if order_payload.get("paymentMethod"):
        form_data["payment_method"] = order_payload.get("paymentMethod")

    return form_data


def invoke_makypay_collection(order_payload):
    if not is_makypay_configured():
        return {
            "status": "demo",
            "message": "MakPay credentials are not configured. Demo checkout is active.",
            "demo": True,
            "data": {
                "transaction": {
                    "reference": str(order_payload.get("reference") or order_payload.get("id") or uuid.uuid4()),
                    "status": "processing",
                }
            },
        }

    try:
        form_data = build_makypay_body(order_payload)
        request = Request(
            f"{MAKYPAY_API_BASE_URL}/collections/collect-money",
            data=urlencode(form_data).encode("utf-8"),
            headers={
                "Authorization": f"Basic {MAKYPAY_BASE64_HEADER}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {"status": "success", "data": {}}
            try:
                return json.loads(body)
            except Exception:
                return {"status": "success", "raw": body}
    except (HTTPError, URLError) as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        return {
            "status": "demo",
            "message": "MakPay request failed. Falling back to the local demo flow.",
            "demo": True,
            "details": details,
        }
    except Exception as exc:
        return {
            "status": "demo",
            "message": "MakPay request failed. Falling back to the local demo flow.",
            "demo": True,
            "details": str(exc),
        }


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/api/products":
            self.send_json(get_products())
            return

        if self.path == "/api/orders":
            self.send_json(get_orders())
            return

        if self.path == "/api/makypay/config":
            self.send_json(
                {
                    "configured": is_makypay_configured(),
                    "successUrl": MAKYPAY_SUCCESS_URL,
                    "cancelUrl": MAKYPAY_CANCEL_URL,
                    "baseUrl": MAKYPAY_API_BASE_URL,
                    "webhookUrl": "https://czafashions.com/webhooks/makypay",
                }
            )
            return

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/products":
            payload = self.read_json_body()
            if isinstance(payload, list):
                save_products(payload)
                self.send_json({"ok": True, "count": len(payload)})
                return

            self.send_json({"ok": False, "error": "Expected a JSON array."}, status=400)
            return

        if self.path == "/api/orders":
            payload = self.read_json_body()
            if isinstance(payload, list):
                save_orders(payload)
                self.send_json({"ok": True, "count": len(payload)})
                return

            self.send_json({"ok": False, "error": "Expected a JSON array."}, status=400)
            return

        if self.path == "/api/makypay/collect":
            payload = self.read_json_body()
            if not isinstance(payload, dict):
                self.send_json({"ok": False, "error": "Expected a JSON object."}, status=400)
                return
            response = invoke_makypay_collection(payload)
            self.send_json(response)
            return

        if self.path == "/webhooks/makypay":
            payload = self.read_json_body()
            if not isinstance(payload, dict):
                self.send_json({"ok": False, "error": "Expected a JSON object."}, status=400)
                return

            event_type = payload.get("event_type")
            if event_type == "collection.completed":
                reference = payload.get("transaction", {}).get("reference")
                orders = get_orders()
                updated = False

                for order in orders:
                    if str(order.get("reference") or order.get("id") or "") == str(reference):
                        order["status"] = "Paid"
                        order["paymentStatus"] = "completed"
                        order["paymentProvider"] = payload.get("collection", {}).get("provider", "makypay")
                        order["paidAt"] = payload.get("metadata", {}).get("response_timestamp")
                        updated = True

                if updated:
                    save_orders(orders)

                self.send_json({"ok": True, "updated": updated, "event_type": event_type})
                return

            self.send_json({"ok": True, "ignored": True, "event_type": event_type})
            return

        self.send_json({"ok": False, "error": "Not found."}, status=404)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    ensure_json(DATA_DIR / "products.json", DEFAULT_PRODUCTS)
    ensure_json(DATA_DIR / "orders.json", [])
    ensure_database()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Serving CZA site on http://{host}:{port}")
    httpd.serve_forever()
