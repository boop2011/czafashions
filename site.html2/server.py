from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen
import hashlib
import hmac
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
).strip()
MAKYPAY_SECRET_KEY = os.getenv("MAKYPAY_SECRET_KEY", "maky_v1_sec_ZUl7RpZ4SEtW5FPUk38qGQwwSA6OPjQ6").strip()
MAKYPAY_API_BASE_URL = os.getenv("MAKYPAY_API_BASE_URL", "https://wire-api.makylegacy.com/api/v1")
MAKYPAY_SUCCESS_URL = os.getenv("MAKYPAY_SUCCESS_URL", "https://czafashions.com/shop")
MAKYPAY_CANCEL_URL = os.getenv("MAKYPAY_CANCEL_URL", "https://czafashions.com/shop")
MAKYPAY_WEBHOOK_SECRET = os.getenv("MAKYPAY_WEBHOOK_SECRET", "")
MAKYPAY_WEBHOOK_TOKEN = os.getenv("MAKYPAY_WEBHOOK_TOKEN", "")
DODO_API_SECRET = os.getenv("DODO_API_SECRET", "cRKy0MNHs-pLl7s_.1GiTxYMGecFsuVKl5dDNGgQWgEKaThahLrSF_GlZcoPi0Teh").strip()
DODO_BUSINESS_ID = os.getenv("DODO_BUSINESS_ID", "").strip()
DODO_API_BASE_URL = os.getenv("DODO_API_BASE_URL", "https://api.dodopayments.com/v1")
JJUMA_PUBLIC_KEY = os.getenv("JJUMA_PUBLIC_KEY", "bp_live_pub_eae02fdfbff5e103288f2fa5cf35f21a").strip()
JJUMA_SECRET_KEY = os.getenv("JJUMA_SECRET_KEY", "bp_live_sec_925e13de1e9700b63c3bfb05c9558902bc010db89f7ffbd4").strip()
JJUMA_WEBHOOK_SECRET = os.getenv("JJUMA_WEBHOOK_SECRET", "whsec_98c797dee4be7468f3bfbe1eb015328be16cb140eb5ba703").strip()
JJUMA_API_BASE_URL = os.getenv("JJUMA_API_BASE_URL", "https://api.jjuma.com").strip()
JJUMA_SUCCESS_URL = os.getenv("JJUMA_SUCCESS_URL", "https://czafashions.com/checkout.html?payment=success").strip()
JJUMA_CANCEL_URL = os.getenv("JJUMA_CANCEL_URL", "https://czafashions.com/checkout.html?payment=failed").strip()
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_ADMIN_NUMBER = os.getenv("WHATSAPP_ADMIN_NUMBER", "256746803321").strip()
WHATSAPP_API_BASE_URL = os.getenv("WHATSAPP_API_BASE_URL", "https://graph.facebook.com/v20.0").strip()


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


def normalize_whatsapp_number(phone_number):
    if not phone_number:
        return ""

    digits = "".join(ch for ch in str(phone_number) if ch.isdigit())
    if not digits:
        return ""

    if digits.startswith("256"):
        return digits

    if digits.startswith("0"):
        return f"256{digits[1:]}"

    return digits


def build_whatsapp_order_message(order):
    items = order.get("items") or []
    item_lines = []
    for item in items:
        item_name = str(item.get("name") or "Item").strip()
        qty = int(item.get("qty") or 1)
        item_price = float(item.get("price") or 0)
        item_lines.append(f"- {item_name} x{qty} ({item_price * qty})")

    delivery_address = order.get("deliveryAddress") or order.get("delivery_address") or "Not provided"
    delivery_city = order.get("deliveryCity") or order.get("delivery_city") or "Not provided"
    delivery_country = order.get("deliveryCountry") or order.get("delivery_country") or "Not provided"
    phone_number = order.get("customerPhone") or order.get("customer_phone") or "Not provided"
    customer_name = order.get("customerName") or order.get("customer_name") or "Customer"

    item_section = item_lines if item_lines else ["No items listed"]

    lines = [
        "New order received from CZA Store.",
        "",
        f"Customer: {customer_name}",
        f"Phone: {phone_number}",
        f"Email: {order.get('customerEmail') or 'Not provided'}",
        f"Delivery address: {delivery_address}",
        f"City: {delivery_city}",
        f"Country: {delivery_country}",
        f"Delivery notes: {order.get('deliveryNotes') or order.get('delivery_notes') or 'None'}",
        "",
        "Items:",
    ]
    lines.extend(item_section)
    lines.extend([
        "",
        f"Total: {order.get('currency', 'UGX')} {order.get('total', 0)}",
        f"Order ID: {order.get('id', 'N/A')}",
        f"Confirmation link: {order.get('confirmationLink') or 'Not provided'}",
    ])
    return "\n".join(lines)


def send_whatsapp_order_notification(order):
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return {"sent": False, "reason": "WhatsApp credentials are not configured."}

    admin_number = normalize_whatsapp_number(WHATSAPP_ADMIN_NUMBER)
    if not admin_number:
        return {"sent": False, "reason": "WhatsApp admin number is missing."}

    message = build_whatsapp_order_message(order)
    payload = {
        "messaging_product": "whatsapp",
        "to": admin_number,
        "type": "text",
        "text": {"body": message},
    }

    try:
        request = Request(
            f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8", errors="ignore")
            return {"sent": True, "response": response_body}
    except Exception as exc:
        return {"sent": False, "error": str(exc)}


def is_makypay_configured():
    base64_header = (MAKYPAY_BASE64_HEADER or "").strip()
    secret_key = (MAKYPAY_SECRET_KEY or "").strip()
    return bool(
        base64_header
        and secret_key
        and base64_header != "YOUR_BASE64_HEADER"
        and not secret_key.startswith("your_")
        and secret_key != "demo"
    )


def is_dodo_configured():
    secret_key = (DODO_API_SECRET or "").strip()
    return bool(secret_key and secret_key != "demo" and not secret_key.startswith("your_"))


def is_jjuma_configured():
    public_key = (JJUMA_PUBLIC_KEY or "").strip()
    secret_key = (JJUMA_SECRET_KEY or "").strip()
    webhook_secret = (JJUMA_WEBHOOK_SECRET or "").strip()
    return bool(
        public_key
        and secret_key
        and webhook_secret
        and public_key != "demo"
        and secret_key != "demo"
        and not public_key.startswith("your_")
        and not secret_key.startswith("your_")
        and not webhook_secret.startswith("your_")
    )


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


def get_webhook_url():
    base_url = "https://czafashions.com/webhooks/makypay"
    if MAKYPAY_WEBHOOK_TOKEN:
        return f"{base_url}?secret={quote(MAKYPAY_WEBHOOK_TOKEN, safe='')}"
    return base_url


def get_webhook_secret_from_path(request_path):
    parsed = urlparse(request_path)
    query_params = parse_qs(parsed.query)
    values = query_params.get("secret", [])
    return values[0] if values else ""


def extract_transaction_reference(payload):
    if not isinstance(payload, dict):
        return ""

    transaction = payload.get("transaction")
    if isinstance(transaction, dict):
        reference = transaction.get("reference") or transaction.get("uuid")
        if reference:
            return str(reference)

    reference = payload.get("reference") or payload.get("uuid")
    return str(reference) if reference else ""


def normalize_verified_status(payload):
    if not isinstance(payload, dict):
        return "unknown"

    if payload.get("status"):
        return str(payload.get("status")).lower()

    transaction = payload.get("transaction")
    if isinstance(transaction, dict) and transaction.get("status"):
        return str(transaction.get("status")).lower()

    data = payload.get("data")
    if isinstance(data, dict) and data.get("status"):
        return str(data.get("status")).lower()

    return "unknown"


def verify_makypay_transaction(reference):
    if not reference:
        return {"verified": False, "status": "unknown", "message": "Missing transaction reference."}

    if not is_makypay_configured():
        return {
            "verified": False,
            "status": "demo",
            "message": "MakPay credentials are not configured. Demo checkout is active.",
        }

    try:
        request = Request(
            f"{MAKYPAY_API_BASE_URL}/collections/collect-money/{reference}",
            headers={
                "Authorization": f"Basic {MAKYPAY_BASE64_HEADER}",
                "Accept": "application/json",
            },
            method="GET",
        )

        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {"verified": False, "status": "unknown", "message": "Blank response from MakPay."}

            try:
                payload = json.loads(body)
                return {
                    "verified": True,
                    "status": normalize_verified_status(payload),
                    "data": payload,
                }
            except Exception as exc:
                return {"verified": False, "status": "unknown", "message": f"Unable to parse MakPay response: {exc}"}
    except (HTTPError, URLError) as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        return {
            "verified": False,
            "status": "error",
            "message": "Unable to verify the transaction with MakPay.",
            "details": details,
        }
    except Exception as exc:
        return {
            "verified": False,
            "status": "error",
            "message": "Unable to verify the transaction with MakPay.",
            "details": str(exc),
        }


def update_verified_order(reference, verified_status, provider="makypay", paid_at=None):
    orders = get_orders()
    updated = False

    for order in orders:
        if str(order.get("reference") or order.get("id") or "") != str(reference):
            continue

        if verified_status == "completed":
            order["status"] = "Paid"
            order["paymentStatus"] = "completed"
            order["paymentProvider"] = provider
            if paid_at:
                order["paidAt"] = paid_at
        else:
            order["status"] = "Payment failed"
            order["paymentStatus"] = verified_status
            order["paymentProvider"] = provider

        updated = True

    if updated:
        save_orders(orders)

    return updated


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

    candidate_reference = order_payload.get("reference") or order_payload.get("id")
    if candidate_reference and str(candidate_reference).count("-") == 4:
        reference = str(candidate_reference)
    else:
        reference = str(uuid.uuid4())

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


def create_dodo_payment_intent(order_payload):
    if not is_dodo_configured():
        return {
            "ok": False,
            "error": "Dodo Payments credentials are not configured.",
        }

    try:
        request_body = {
            "amount": int(order_payload.get("amount", 0)),
            "currency": order_payload.get("currency", "UGX"),
            "description": f"Order from CZA - {order_payload.get('customerName', 'Customer')}",
            "customerEmail": order_payload.get("customerEmail", ""),
            "customerPhone": order_payload.get("customerPhone", ""),
            "metadata": {
                "orderId": order_payload.get("id"),
                "customerName": order_payload.get("customerName", "Customer"),
                "deliveryAddress": order_payload.get("deliveryAddress", ""),
                "items": order_payload.get("items", []),
            },
        }

        if DODO_BUSINESS_ID:
            request_body["businessId"] = DODO_BUSINESS_ID

        request = Request(
            f"{DODO_API_BASE_URL}/payments/intents",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DODO_API_SECRET}",
            },
            method="POST",
        )

        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {"ok": True, "data": {}}
            try:
                return {"ok": True, "data": json.loads(body)}
            except Exception:
                return {"ok": True, "data": {"raw": body}}
    except (HTTPError, URLError) as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        return {"ok": False, "error": details or "Unable to create Dodo payment intent."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def build_jjuma_payment_payload(order_payload):
    order_id = str(order_payload.get("id") or order_payload.get("orderId") or uuid.uuid4())
    amount_value = order_payload.get("amount")
    if amount_value in (None, ""):
        amount_value = order_payload.get("total") or 0

    amount = int(float(amount_value or 0))
    currency = "UGX"
    customer_name = str(order_payload.get("customerName") or order_payload.get("customer_name") or "Customer").strip()
    payment_method = str(order_payload.get("paymentMethod") or order_payload.get("payment_method") or "card").strip().lower()

    return {
        "amount": amount,
        "currency": currency,
        "description": f"Order from CZA - {customer_name}",
        "customer_name": customer_name,
        "customer_email": order_payload.get("customerEmail") or order_payload.get("customer_email") or "",
        "customer_phone": order_payload.get("customerPhone") or order_payload.get("customer_phone") or "",
        "customer_address": order_payload.get("deliveryAddress") or "",
        "payment_method": payment_method,
        "redirect_url": JJUMA_SUCCESS_URL,
        "return_url": JJUMA_SUCCESS_URL,
        "cancel_redirect_url": JJUMA_CANCEL_URL,
        "webhook_url": f"https://czafashions.com/webhooks/jjuma",
        "metadata": {
            "order_id": order_id,
            "customer_name": customer_name,
            "delivery_address": order_payload.get("deliveryAddress") or "",
            "items": order_payload.get("items", []),
            "payment_method": payment_method,
        },
        "external_order_id": order_id,
        "idempotency_key": f"order-{order_id}-{uuid.uuid4()}",
    }


def create_jjuma_payment(order_payload):
    if not is_jjuma_configured():
        return {"ok": False, "error": "JJuma live credentials are not configured."}

    try:
        request_body = build_jjuma_payment_payload(order_payload)
        request = Request(
            f"{JJUMA_API_BASE_URL}/api/v1/payments/create",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {JJUMA_PUBLIC_KEY}",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {"ok": True, "data": {}}
            try:
                data = json.loads(body)
                return {"ok": True, "data": data}
            except Exception:
                return {"ok": True, "data": {"raw": body}}
    except (HTTPError, URLError) as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        return {"ok": False, "error": details or "Unable to create JJuma payment."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_jjuma_payment(transaction_id):
    if not is_jjuma_configured():
        return {"verified": False, "status": "disabled", "message": "JJuma live credentials are not configured."}

    if not transaction_id:
        return {"verified": False, "status": "unknown", "message": "Missing transaction id."}

    try:
        request = Request(
            f"{JJUMA_API_BASE_URL}/api/v1/payments/verify/{quote(str(transaction_id))}",
            headers={
                "Authorization": f"Bearer {JJUMA_SECRET_KEY}",
                "Accept": "application/json",
            },
            method="GET",
        )

        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {"verified": False, "status": "unknown", "message": "Blank response from JJuma verification."}

            try:
                payload = json.loads(body)
                status = str(payload.get("status") or payload.get("data", {}).get("status") or "unknown").lower()
                return {"verified": True, "status": status, "data": payload}
            except Exception as exc:
                return {"verified": False, "status": "unknown", "message": f"Unable to parse JJuma response: {exc}"}
    except (HTTPError, URLError) as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        return {"verified": False, "status": "error", "message": "Unable to verify the JJuma transaction.", "details": details}
    except Exception as exc:
        return {"verified": False, "status": "error", "message": "Unable to verify the JJuma transaction.", "details": str(exc)}


def verify_jjuma_signature(raw_body, timestamp, signature):
    if not raw_body or not timestamp or not signature or not JJUMA_WEBHOOK_SECRET:
        return False

    forwarded_signature = signature.strip().removeprefix("sha256=")
    if not forwarded_signature:
        return False

    expected_signature = hmac.new(
        JJUMA_WEBHOOK_SECRET.encode("utf-8"),
        f"{timestamp}.{raw_body.decode('utf-8', errors='ignore')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, forwarded_signature)


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
                    "webhookUrl": get_webhook_url(),
                    "webhookTokenConfigured": bool(MAKYPAY_WEBHOOK_TOKEN),
                }
            )
            return

        if self.path == "/api/dodo/config":
            self.send_json(
                {
                    "configured": is_dodo_configured(),
                    "businessId": DODO_BUSINESS_ID,
                    "baseUrl": "/api/dodo",
                }
            )
            return

        if self.path == "/api/jjuma/config":
            self.send_json(
                {
                    "configured": is_jjuma_configured(),
                    "baseUrl": "/api/jjuma",
                    "apiBaseUrl": JJUMA_API_BASE_URL,
                    "successUrl": JJUMA_SUCCESS_URL,
                    "cancelUrl": JJUMA_CANCEL_URL,
                }
            )
            return

        if self.path.startswith("/api/jjuma/verify"):
            transaction_id = parse_qs(urlparse(self.path).query).get("transaction_id", [""])[0]
            self.send_json(verify_jjuma_payment(transaction_id))
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
                latest_order = payload[0] if payload else None
                whatsapp_result = send_whatsapp_order_notification(latest_order) if isinstance(latest_order, dict) else {"sent": False, "reason": "No order payload available."}
                self.send_json({"ok": True, "count": len(payload), "whatsapp": whatsapp_result})
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

        if self.path == "/api/dodo/create-intent":
            payload = self.read_json_body()
            if not isinstance(payload, dict):
                self.send_json({"ok": False, "error": "Expected a JSON object."}, status=400)
                return

            result = create_dodo_payment_intent(payload)
            if result.get("ok"):
                self.send_json(result.get("data", {}))
                return

            self.send_json({"error": result.get("error", "Unable to create Dodo payment intent.")}, status=502)
            return

        if self.path == "/api/jjuma/create-payment":
            payload = self.read_json_body()
            if not isinstance(payload, dict):
                self.send_json({"ok": False, "error": "Expected a JSON object."}, status=400)
                return

            result = create_jjuma_payment(payload)
            if result.get("ok"):
                self.send_json(result.get("data", {}))
                return

            self.send_json({"error": result.get("error", "Unable to create JJuma payment.")}, status=502)
            return

        if self.path.startswith("/webhooks/jjuma"):
            raw_body = self.read_raw_body()
            if not raw_body:
                self.send_json({"ok": False, "error": "Expected a raw JSON body."}, status=400)
                return

            timestamp = self.headers.get("X-Jjuma-Timestamp", "")
            signature = self.headers.get("X-Jjuma-Signature", "")
            if not verify_jjuma_signature(raw_body, timestamp, signature):
                self.send_json({"ok": False, "error": "Invalid JJuma webhook signature."}, status=401)
                return

            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self.send_json({"ok": False, "error": "Invalid JJuma webhook JSON."}, status=400)
                return

            event_name = str(payload.get("event") or payload.get("event_type") or payload.get("data", {}).get("event") or "").strip()
            if not event_name:
                event_name = str(payload.get("payment_status") or payload.get("status") or "unknown").strip()

            reference = str(payload.get("reference") or payload.get("tx_ref") or payload.get("data", {}).get("reference") or payload.get("data", {}).get("tx_ref") or "").strip()
            transaction_id = str(payload.get("transaction_id") or payload.get("data", {}).get("transaction_id") or "").strip()
            verified_status = str(payload.get("payment_status") or payload.get("status") or payload.get("data", {}).get("payment_status") or payload.get("data", {}).get("status") or "unknown").lower()

            if reference:
                updated = update_verified_order(reference, verified_status, "jjuma", payload.get("timestamp") or payload.get("data", {}).get("timestamp"))
            else:
                updated = False

            self.send_json(
                {
                    "ok": True,
                    "verified": True,
                    "updated": updated,
                    "event": event_name,
                    "reference": reference,
                    "transaction_id": transaction_id,
                    "transaction_status": verified_status,
                }
            )
            return

        if self.path.startswith("/webhooks/makypay"):
            if MAKYPAY_WEBHOOK_TOKEN and get_webhook_secret_from_path(self.path) != MAKYPAY_WEBHOOK_TOKEN:
                self.send_json({"ok": False, "error": "Unauthorized webhook request."}, status=401)
                return

            payload = self.read_json_body()
            if not isinstance(payload, dict):
                self.send_json({"ok": False, "error": "Expected a JSON object."}, status=400)
                return

            event_type = payload.get("event_type")
            reference = extract_transaction_reference(payload)
            if not reference:
                self.send_json({"ok": False, "error": "Missing transaction reference in webhook payload."}, status=400)
                return

            verification = verify_makypay_transaction(reference)
            if not verification.get("verified"):
                self.send_json(
                    {
                        "ok": False,
                        "verified": False,
                        "reference": reference,
                        "event_type": event_type,
                        "message": verification.get("message", "Unable to verify transaction."),
                        "details": verification.get("details", ""),
                    },
                    status=400,
                )
                return

            verified_status = verification.get("status", "unknown")
            provider = payload.get("collection", {}).get("provider", "makypay") if isinstance(payload.get("collection"), dict) else "makypay"
            paid_at = None
            if isinstance(payload.get("metadata"), dict):
                paid_at = payload.get("metadata", {}).get("response_timestamp")

            if verified_status == "completed":
                updated = update_verified_order(reference, verified_status, provider, paid_at)
                self.send_json({"ok": True, "verified": True, "updated": updated, "event_type": event_type, "reference": reference, "transaction_status": verified_status})
                return

            if verified_status in {"failed", "cancelled", "expired", "declined"}:
                updated = update_verified_order(reference, verified_status, provider, paid_at)
                self.send_json({"ok": True, "verified": True, "updated": updated, "event_type": event_type, "reference": reference, "transaction_status": verified_status})
                return

            self.send_json(
                {
                    "ok": True,
                    "verified": True,
                    "ignored": True,
                    "event_type": event_type,
                    "reference": reference,
                    "transaction_status": verified_status,
                }
            )
            return

        self.send_json({"ok": False, "error": "Not found."}, status=404)

    def read_raw_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def read_json_body(self):
        body = self.read_raw_body()
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
