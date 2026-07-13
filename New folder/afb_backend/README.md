# American Food & Beverage — Operations Backend

A complete backend for running the business day-to-day: customers, product catalog,
inventory, order lifecycle, packing, shipping/delivery tracking, and reporting.

Built with **FastAPI + SQLite** — no external database or cloud account needed to run it.
SQLite is a real, production-capable database (used by companies at real scale); if you
outgrow it later, the same SQLAlchemy models port to Postgres/MySQL with a one-line
connection-string change.

---

## What's included

- `app/models.py` — the full database schema (customers, products, inventory,
  inventory transactions/audit log, orders, order items, order status history,
  packing records, shipments, shipment tracking events)
- `app/routers/` — the REST API: customers, products, inventory, orders, packing,
  shipping, reports
- `seed.py` — loads your product catalog plus a handful of sample customers/orders
  moving through every stage, so the reports have real data to show immediately
- `dashboard.html` — a reporting dashboard that reads live from the API (inventory,
  order status breakdown, cycle-time, top customers, shipping performance, packing
  productivity)

## How the pieces connect

```
Customer places order
   → inventory reserved (qty_reserved goes up)
Staff packs it
   → POST /orders/{id}/packing  → order_items.qty_packed updated, status → packing/packed
Staff ships it
   → POST /orders/{id}/shipment → inventory deducted for real, status → out_for_delivery
Carrier delivers
   → POST /shipments/{id}/events {"status":"delivered"} → status → delivered
```

Every status change is logged to `order_status_history` with a timestamp — that's
what powers the cycle-time report (average hours between each stage).

---

## Run it

Requires Python 3.10+.

```bash
cd afb_backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python seed.py                  # creates afb.db with your catalog + sample orders

# By default this seeds a fictional demo catalog. To use the REAL
# American Food & Beverage catalog instead: export products from Magento
# as catalog.csv (columns: sku,category,name,pack_size,price,qty_on_hand —
# only category and name are required) and drop it in this folder before
# running seed.py. It's picked up automatically. See seed.py's docstring
# for details, and `python seed.py --catalog-only` to reload just the
# catalog without wiping existing customers/orders.
uvicorn app.main:app --reload   # starts the API on http://127.0.0.1:8000
```

Once it's running, everything is served from that one address:

- **http://127.0.0.1:8000/order** — customer-facing ordering + tracking site
- **http://127.0.0.1:8000/dashboard** — operations/reporting dashboard
- **http://127.0.0.1:8000/docs** — interactive API docs, try any endpoint from the browser

Both `/order` and `/dashboard` call the API using same-origin requests, so
whatever address you reach the server on (localhost, or your laptop's LAN IP
below) is automatically the address they talk to — no config file to edit.

---

## Running this live on a client's network (consultant demo / pilot)

To let people on other workstations place orders and watch them land on your
laptop's dashboard in real time:

**1. Start the server bound to your network interface, not just localhost:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` is what makes it reachable from other machines. Without it,
uvicorn only accepts connections from your own laptop.

**2. Find your laptop's IP address on that network:**

```bash
# macOS
ipconfig getifaddr en0        # Wi-Fi — try en1 if en0 gives nothing

# Windows (PowerShell or cmd)
ipconfig                      # look for "IPv4 Address" under your active adapter

# Linux
hostname -I
```

You'll get something like `192.168.1.42`.

**3. Allow the connection through your firewall.** macOS and Windows will
usually prompt you the first time something tries to reach port 8000 —
approve it. If you don't get a prompt, you may need to add an inbound rule
manually (Windows Defender Firewall → Advanced Settings → Inbound Rules → new
rule for port 8000).

**4. On any other workstation on the same network**, open a browser to:

```
http://192.168.1.42:8000/order        (use your actual IP from step 2)
http://192.168.1.42:8000/dashboard
```

That's it — every order placed from any machine hits the same database on
your laptop, and your dashboard updates live.

### Things worth knowing before you rely on this for the live session

- **Corporate/guest Wi-Fi sometimes blocks device-to-device traffic** ("client
  isolation" or "AP isolation"), even though everyone's on the same network —
  common on guest networks and locked-down corporate Wi-Fi. If workstations
  can't reach your laptop, this is the most likely cause; ask the client's IT
  contact, or use a dedicated hotspot/router you control for the demo instead.
- **Your laptop is the whole system for the duration of the demo.** If it
  sleeps, loses Wi-Fi, or you close the lid, the site goes down for everyone.
  Disable sleep/screen-lock networking suspension for the session.
- **There's no login on any endpoint yet** — anyone who can reach that IP can
  hit any part of the API, including status updates. Fine for a controlled
  demo room; not something to leave running unattended on a real client
  network afterward.
- **This is a live pilot, not a resilient production deployment.** No backups
  are happening automatically — if you want to preserve what happened during
  the session, copy `afb.db` somewhere afterward (`cp afb.db afb-demo-backup.db`).

> Re-running `python seed.py` wipes and rebuilds `afb.db` from scratch — use it
> to reset to a clean demo state. Once you're using this for real, don't run it
> again (it would erase real data). Back up `afb.db` regularly instead.

---

## API reference

### Customers
- `POST /customers` — create (or return existing by email)
- `GET /customers` — list all
- `GET /customers/{id}`

### Products
- `POST /products` — create, with `initial_qty` and `reorder_threshold`
- `GET /products?category=...` — list, optional category filter

### Inventory
- `GET /inventory?low_stock_only=true` — current stock levels
- `GET /inventory/{product_id}`
- `POST /inventory/{product_id}/adjust` — manual adjustment (receiving stock,
  damage write-off, cycle-count correction, etc.)
- `GET /inventory/{product_id}/transactions` — full audit trail for a product

### Orders
- `POST /orders` — place an order (creates/reuses the customer, reserves stock)
- `GET /orders?status=packing` — list, optional status filter
- `GET /orders/{order_number}` — full detail incl. status history
- `PATCH /orders/{order_number}/status` — move to any status (cancelling
  automatically releases reserved inventory)

### Packing
- `POST /orders/{order_number}/packing` — log who packed it, how many boxes,
  and (optionally) exact per-item quantities packed
- `GET /orders/{order_number}/packing` — packing history for that order

### Shipping & delivery tracking
- `POST /orders/{order_number}/shipment` — ship it (deducts inventory for real,
  order status → `out_for_delivery`)
- `POST /shipments/{id}/events` — add a tracking event (`in_transit`,
  `delivered`, `exception`, or any custom status/location update)
- `GET /orders/{order_number}/shipment` — shipment + full event history

### Reports
- `GET /reports/dashboard` — headline KPIs
- `GET /reports/inventory` — full stock report with low-stock flags and
  estimated value (once you fill in `unit_price` on products)
- `GET /reports/orders-by-status` — order counts per status
- `GET /reports/order-cycle-time` — average hours spent in each stage, and
  average total received→delivered time
- `GET /reports/customers/top` — ranked by order volume
- `GET /reports/shipping` — performance by carrier (shipment count, delivered
  count, average transit time)
- `GET /reports/packing-productivity` — orders/boxes packed per staff member

---

## What this is (and isn't) yet

This is a **real, working backend** — every endpoint above was tested end-to-end
(order created → confirmed → packed → shipped → delivered, with inventory moving
correctly at each step) before this was handed to you. It's suitable for actually
running the business from a single machine or a small internal server.

To go further, the natural next steps are:

1. **Deploy it somewhere reachable** — right now it only runs on your own
   machine (`127.0.0.1`). Hosting it (Render, Railway, Fly.io, or your own
   server) gives you a real URL your team and customers' tracking page can
   reach from anywhere.
2. **Connect the customer-facing ordering site** — the order/track website
   built earlier can point at this API instead of the browser's local storage,
   so orders customers place actually land here, and tracking reflects real
   status updates from your team.
3. **Add authentication** — right now anyone with the URL can call any
   endpoint. Before this is public, it needs login/API-key protection,
   especially on the write endpoints (creating orders is fine to leave open;
   updating status, packing, and shipping should be staff-only).
4. **Move to Postgres** if you outgrow a single SQLite file (multiple people
   writing at once, need automated backups/replication) — the model code
   doesn't need to change, just the connection string.

Happy to help with any of these next.
