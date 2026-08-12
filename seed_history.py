"""
seed_history.py — Back-fill 6 months of realistic order, customer, and return
history so the Executive View dashboard has meaningful trend data to display.

This script is ADDITIVE — it does NOT wipe existing data. Run it once after
seed.py has already populated the catalog and base customers/orders.

Usage:
    python seed_history.py          # adds 6 months of back-dated history
    python seed_history.py --months 9   # override the number of months

Revenue trajectory is calibrated to reflect a business recovering from a
plateau and building toward the $6M annual target:
  - 6 months ago: ~$210K/month  (~$2.5M annualized)
  - Most recent complete month: ~$400K/month  (~$4.8M annualized)
  - Growth curve: roughly 10-12% MoM acceleration
"""
import random
import sys
from datetime import datetime, timedelta, date

from app.database import SessionLocal
from app import models

random.seed(42)

# ─── Configuration ────────────────────────────────────────────────────────────

MONTHS_BACK = 6   # how many months of history to generate

# Revenue targets per month (oldest → newest).  Tweak to tell whatever story
# is most useful for the demo.
MONTHLY_REVENUE_TARGETS = [
    210_000,   # month -6
    238_000,   # month -5
    265_000,   # month -4
    305_000,   # month -3
    355_000,   # month -2
    398_000,   # month -1  (last full month)
]

# Approx order size in cases and unit price bracket
CASES_PER_ORDER = (8, 30)      # random.randint range
UNIT_PRICE_RANGE = (45, 90)    # per case, fallback if product has no price

# New customers to create per month (they accumulate realistically)
NEW_CUSTOMERS_PER_MONTH = [3, 2, 4, 3, 5, 4]

# Returns: qty cases returned per month
RETURNS_PER_MONTH = [8, 6, 11, 7, 9, 12]

CARRIERS = ["AFB Fleet", "Private Trucking Partner", "Regional Carrier"]
PACKERS  = ["Luis M.", "Dana K.", "Marco R.", "Aisha T."]
RETURN_REASONS = [
    models.ReturnReason.damaged,
    models.ReturnReason.expired,
    models.ReturnReason.wrong_item,
    models.ReturnReason.quality_issue,
    models.ReturnReason.customer_refused,
]

ORDER_SEQ_START = 5000   # start numbering historical orders here to avoid collisions

# ─── Helpers ──────────────────────────────────────────────────────────────────

def month_window(year, month):
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return start, end

def rand_dt(start, end):
    """Random datetime between start and end."""
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta * 0.85))

def build_month_list(n):
    """Return list of (year, month) tuples, oldest first, ending at last complete month."""
    now = datetime.utcnow()
    # last complete month
    if now.month == 1:
        anchor_y, anchor_m = now.year - 1, 12
    else:
        anchor_y, anchor_m = now.year, now.month - 1

    months = []
    for i in range(n - 1, -1, -1):
        m = (anchor_m - i - 1) % 12 + 1
        y = anchor_y - ((anchor_m - i - 1) // 12)
        months.append((y, m))
    return months

def make_order_number(seq):
    return f"ORD-H{seq:04d}"

# ─── Main seeding logic ────────────────────────────────────────────────────────

def run(months_back=MONTHS_BACK):
    db = SessionLocal()
    try:
        products = (
            db.query(models.Product)
            .filter(models.Product.item_type == models.ProductType.sellable,
                    models.Product.active == True)
            .all()
        )
        if not products:
            print("No sellable products found — run seed.py first.")
            return

        month_list = build_month_list(months_back)
        print(f"Generating history for {len(month_list)} months: "
              f"{month_list[0][1]}/{month_list[0][0]} → {month_list[-1][1]}/{month_list[-1][0]}")

        # Ensure we have customers to assign orders to — create historical
        # ones first so they appear in the right month.
        existing_customers = db.query(models.Customer).all()
        historical_customers = []   # track across months for reuse

        order_seq = ORDER_SEQ_START
        # Adjust seq upward if historical orders already exist
        existing_nums = [
            int(o.order_number.replace("ORD-H", ""))
            for o in db.query(models.Order).all()
            if o.order_number.startswith("ORD-H")
        ]
        if existing_nums:
            order_seq = max(existing_nums) + 1

        for idx, (year, month) in enumerate(month_list):
            start, end = month_window(year, month)
            target_rev = MONTHLY_REVENUE_TARGETS[idx] if idx < len(MONTHLY_REVENUE_TARGETS) else 300_000
            new_cust_count = NEW_CUSTOMERS_PER_MONTH[idx] if idx < len(NEW_CUSTOMERS_PER_MONTH) else 3
            return_qty_target = RETURNS_PER_MONTH[idx] if idx < len(RETURNS_PER_MONTH) else 8

            label = date(year, month, 1).strftime("%b %Y")
            print(f"  [{label}] target revenue ${target_rev:,.0f} ...")

            # ── Create new customers for this month ──
            month_new_customers = []
            for c_i in range(new_cust_count):
                cust_dt = rand_dt(start, end)
                email_base = f"hist.customer.{year}{month:02d}.{c_i}@demo.afb"
                existing = db.query(models.Customer).filter(
                    models.Customer.email == email_base
                ).first()
                if existing:
                    month_new_customers.append(existing)
                    continue
                c = models.Customer(
                    name=f"Historical Customer {year}-{month:02d}-{c_i + 1}",
                    company=f"Demo Co {random.randint(100, 999)}",
                    email=email_base,
                    phone=f"555-{random.randint(1000,9999)}",
                    address="123 Demo Street, Demo City, NJ",
                    created_at=cust_dt,
                )
                db.add(c)
                db.flush()
                month_new_customers.append(c)
                historical_customers.append(c)

            # Build pool of customers available for orders this month
            available_customers = list(existing_customers) + historical_customers
            if not available_customers:
                available_customers = month_new_customers

            # ── Create orders to hit revenue target ──
            generated_rev = 0.0
            attempts = 0
            while generated_rev < target_rev * 0.92 and attempts < 200:
                attempts += 1
                customer = random.choice(available_customers)
                order_dt = rand_dt(start, end)

                # Pick 1-4 line items
                n_items = random.randint(1, 4)
                chosen_products = random.sample(products, min(n_items, len(products)))
                items_data = []
                order_rev = 0.0
                for prod in chosen_products:
                    qty = random.randint(*CASES_PER_ORDER)
                    price = prod.unit_price or random.uniform(*UNIT_PRICE_RANGE)
                    items_data.append((prod, qty, round(price, 2)))
                    order_rev += price * qty

                order = models.Order(
                    order_number=make_order_number(order_seq),
                    customer_id=customer.id,
                    status=models.OrderStatus.delivered,
                    created_at=order_dt,
                    updated_at=order_dt + timedelta(days=random.randint(1, 3)),
                )
                db.add(order)
                db.flush()
                order_seq += 1

                for prod, qty, price in items_data:
                    db.add(models.OrderItem(
                        order_id=order.id,
                        product_id=prod.id,
                        qty_ordered=qty,
                        qty_packed=qty,
                        unit_price_snapshot=price,
                    ))

                # Status history: received → confirmed → packing → packed → delivered
                stages = [
                    ("received",         order_dt),
                    ("confirmed",        order_dt + timedelta(hours=random.uniform(1, 6))),
                    ("packing",          order_dt + timedelta(hours=random.uniform(8, 18))),
                    ("packed",           order_dt + timedelta(hours=random.uniform(20, 30))),
                    ("delivered",        order_dt + timedelta(hours=random.uniform(32, 72))),
                ]
                for status_str, ts in stages:
                    db.add(models.OrderStatusHistory(
                        order_id=order.id,
                        status=models.OrderStatus(status_str),
                        changed_at=ts,
                    ))

                # Packing record
                db.add(models.PackingRecord(
                    order_id=order.id,
                    packed_by=random.choice(PACKERS),
                    boxes=random.randint(1, 4),
                    packed_at=order_dt + timedelta(hours=random.uniform(20, 30)),
                ))

                generated_rev += order_rev

            print(f"           → {attempts} orders, ~${generated_rev:,.0f} revenue generated")

            # ── Create returns for this month ──
            returns_added = 0
            ret_qty_remaining = return_qty_target
            while ret_qty_remaining > 0 and available_customers:
                qty = min(random.randint(1, 4), ret_qty_remaining)
                prod = random.choice(products)
                customer = random.choice(available_customers)
                ret_dt = rand_dt(start, end)

                ret = models.CustomerReturn(
                    customer_id=customer.id,
                    product_id=prod.id,
                    qty=qty,
                    reason=random.choice(RETURN_REASONS),
                    notes="Historical return (seeded)",
                    created_by="seed_history.py",
                    created_at=ret_dt,
                )
                db.add(ret)
                returns_added += 1
                ret_qty_remaining -= qty

            print(f"           → {returns_added} return records, {return_qty_target - ret_qty_remaining} qty")

        db.commit()
        print("\nDone. Historical data committed.")
        print("Restart the server and open the dashboard to see the Executive View.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    m = MONTHS_BACK
    for arg in sys.argv[1:]:
        if arg.startswith("--months"):
            try:
                m = int(arg.split("=")[1]) if "=" in arg else int(sys.argv[sys.argv.index(arg) + 1])
            except (IndexError, ValueError):
                pass
    run(months_back=m)
