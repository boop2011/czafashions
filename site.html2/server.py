from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import uuid

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


def normalize_phone_number(phone_number):
    if not phone_number:
        return ""
    value = str(phone_number).strip().replace(" ", "")
    if value.startswith("+"):
        return value[1:]
    return value


def is_makypay_configured():
    return bool(MAKYPAY_BASE64_HEADER and MAKYPAY_BASE64_HEADER != "YOUR_BASE64_HEADER")


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
            products = ensure_json(DATA_DIR / "products.json", DEFAULT_PRODUCTS)
            self.send_json(products)
            return

        if self.path == "/api/orders":
            orders = ensure_json(DATA_DIR / "orders.json", [])
            self.send_json(orders)
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
                (DATA_DIR / "products.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
                self.send_json({"ok": True, "count": len(payload)})
                return

            self.send_json({"ok": False, "error": "Expected a JSON array."}, status=400)
            return

        if self.path == "/api/orders":
            payload = self.read_json_body()
            if isinstance(payload, list):
                (DATA_DIR / "orders.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
                orders = ensure_json(DATA_DIR / "orders.json", [])
                updated = False

                for order in orders:
                    if str(order.get("reference") or order.get("id") or "") == str(reference):
                        order["status"] = "Paid"
                        order["paymentStatus"] = "completed"
                        order["paymentProvider"] = payload.get("collection", {}).get("provider", "makypay")
                        order["paidAt"] = payload.get("metadata", {}).get("response_timestamp")
                        updated = True

                if updated:
                    (DATA_DIR / "orders.json").write_text(json.dumps(orders, indent=2), encoding="utf-8")

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

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Serving CZA site on http://{host}:{port}")
    httpd.serve_forever()
