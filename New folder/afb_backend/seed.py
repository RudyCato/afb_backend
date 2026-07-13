"""
Run once to populate afb.db with:
  - the product catalog + starting inventory
  - a handful of sample customers
  - sample orders moving through every stage (so reports have real data)

CATALOG SOURCE
--------------
By default this seeds a fictional demo catalog so the app has realistic
data to click through. To use the REAL American Food & Beverage catalog
instead, export it from Magento as a CSV named `catalog.csv` and drop it
in this same folder — the script will use it automatically instead of
the demo data.

Expected catalog.csv columns (header row required):
    sku,category,name,pack_size,price,qty_on_hand
Only `category` and `name` are required; everything else is optional
and will be auto-generated (SKU) or randomized (price/qty) if left blank
— handy if your Magento export doesn't have clean values for every field.

Usage:
    python seed.py                 # seed products + sample customers/orders
    python seed.py --catalog-only  # only reload the catalog, keep existing
                                    # customers/orders untouched
"""
import csv
import os
import random
import sys
from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app import models

random.seed(7)

CSV_PATH = os.path.join(os.path.dirname(__file__), "catalog.csv")

# ---- fallback demo catalog, used only if catalog.csv is not present ----
DEMO_CATALOG = [
    ("dried-fruits", "Dried Fruits & Vegetables", [
        ("Apple Rings", "25 lb case"), ("Apricot Turkish #1", "28 lb case"),
        ("Cherries Bing Pitted", "30 lb case"), ("Coconut Shredded", "25 lb case"),
        ("Cranberries", "25 lb case"), ("Dates Medjool Jumbo", "25 lb case"),
        ("Figs Calimyrna Fancy", "25 lb case"), ("Mango Slices", "case"),
        ("Pineapple Chunk", "case"), ("Raisin Golden", "case"),
    ]),
    ("organic", "Organic Items", [
        ("Organic Almonds Roasted Salted", "case"), ("Organic Cashew Roasted Salted", "case"),
        ("Organic Dates Medjool", "case"), ("Organic Walnuts", "case"),
        ("Apple Raisin Walnut Granola", "case"), ("Classic Granola", "case"),
    ]),
    ("nuts", "Nuts", [
        ("Almond Raw", "25 lb case"), ("Almond Roasted Salted", "25 lb case"),
        ("Cashew Roasted Salted", "25 lb case"), ("Macadamia Nuts", "case"),
        ("Mixed Nuts Salted Supreme", "case"), ("Peanut Roasted Salted", "case"),
        ("Pistachio Inshell Salted", "case"), ("Walnuts Halves", "30 lb case"),
        ("Soy Nut Roasted Salted", "25 lb case"), ("Edamame Roasted Salted", "25 lb case"),
    ]),
    ("gourmet-nuts", "Flavored Gourmet Nuts", [
        ("Marcona Almond Salted", "10 lb case"), ("Marcona Almonds with Truffle", "10 lb case"),
        ("Walnuts Caramelized", "10 lb case"), ("Pecans Caramelized", "10 lb case"),
    ]),
    ("trail-mixes", "Trail Mixes", [
        ("Omega 3 Deluxe Mix", "20 lb case"), ("Heart Healthy Mix", "20 lb case"),
        ("Rocky Mountain Mix", "20 lb case"), ("Cajun Hot Mix", "20 lb case"),
        ("Wasabi Wow Mix", "case"), ("Hiker Trail Mix", "case"),
    ]),
    ("grains-beans-seeds", "Beans, Lentils, Peas, Grains & Seeds", [
        ("Chick Peas / Garbanzos", "20 lb case"), ("Dunya Red Quinoa", "20 lb case"),
        ("Chia Seeds", "20 lb case"), ("Red Lentils", "20 lb case"),
    ]),
    ("chocolate", "Chocolate Covered Items", [
        ("Almond Dark Chocolate Covered", "case"), ("Cashew Dark Chocolate Covered", "case"),
        ("Cranberries Dark Chocolate", "case"), ("Pretzels Milk Chocolate", "case"),
    ]),
    ("granola", "Granolas & Crunches", [
        ("Granola - Dark Chocolate", "15 oz"), ("Granola - French Vanilla", "15 oz"),
        ("Honey Roasted Almond Crunch", "case"),
    ]),
    ("candy", "Candy, Pretzels & Gummies", [
        ("Gummy Bears", "20 lb case"), ("Gummy Worms", "20 lb case"),
        ("Sour Patch Kids", "20 lb case"), ("Swedish Fish", "20 lb case"),
        ("Jelly Beans", "16 lb case"), ("Almonds Jordan Assorted", "30 lb case"),
    ]),
    ("health-snacks", "Health Snacks", [
        ("Chips Plantain Salted", "7 oz"), ("Chips Plantain Sweet", "7 oz"),
        ("Chips Banana Sweetened", "5 oz"),
    ]),
    ("containers", "Container & Packaging Programs", [
        ("Tasty Brand Screw Top (14 ct case)", "9-12 oz"),
        ("Nuts To Go Cups (18 ct case)", "4-8 oz"),
        ("Big Presentation Containers (16 ct case)", "10-16 oz"),
    ]),
]

SAMPLE_PACKERS = ["Luis M.", "Dana K.", "Marcus T.", "Elena R.", "Omar S.", "Priya D."]


SAMPLE_CUSTOMERS = [
    dict(name="Jane Rivera", company="Rivera Foods LLC", email="jane@riverafoods.com",
         phone="908-555-0110", address="120 Market St, Jersey City, NJ"),
    dict(name="Marcus Cole", company="Cole Hospitality Group", email="marcus@colehg.com",
         phone="212-555-0144", address="88 Fifth Ave, New York, NY"),
    dict(name="Priya Nair", company="Nair's Corner Grocer", email="priya@nairsgrocer.com",
         phone="973-555-0199", address="45 Elm St, Newark, NJ"),
    dict(name="Tom Alessi", company="Alessi Airline Catering", email="tom@alessicatering.com",
         phone="646-555-0176", address="JFK Cargo Bldg 14, Queens, NY"),
]


def make_sku(cat_id, idx):
    return f"{cat_id[:3].upper()}-{1000 + idx}"


def slugify(text):
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")[:3] or "gen"


def load_catalog_rows():
    """
    Returns a flat list of dicts: {sku, category, name, pack_size, price, qty_on_hand}
    Reads from catalog.csv if present, otherwise expands DEMO_CATALOG into the
    same shape so the rest of the script doesn't care which source was used.
    """
    if os.path.exists(CSV_PATH):
        rows = []
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            missing = {"category", "name"} - set(h.strip().lower() for h in (reader.fieldnames or []))
            if missing:
                sys.exit(f"catalog.csv is missing required column(s): {', '.join(missing)}")
            for i, raw in enumerate(reader, start=1):
                row = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
                if not row.get("name") or not row.get("category"):
                    continue  # skip incomplete rows rather than failing the whole import
                rows.append({
                    "sku": row.get("sku") or make_sku(slugify(row["category"]), i),
                    "category": row["category"],
                    "name": row["name"],
                    "pack_size": row.get("pack_size") or "",
                    "price": float(row["price"]) if row.get("price") else round(random.uniform(18, 95), 2),
                    "qty_on_hand": int(row["qty_on_hand"]) if row.get("qty_on_hand") else random.randint(0, 120),
                })
        print(f"Loaded {len(rows)} products from catalog.csv (real catalog mode)")
        return rows

    # fallback: demo catalog
    rows = []
    idx = 0
    for cat_id, cat_title, items in DEMO_CATALOG:
        for name, pack in items:
            idx += 1
            rows.append({
                "sku": make_sku(cat_id, idx),
                "category": cat_title,
                "name": name,
                "pack_size": pack,
                "price": round(random.uniform(18, 95), 2),
                "qty_on_hand": random.randint(0, 120),
            })
    print(f"catalog.csv not found — seeding {len(rows)} demo products instead (see seed.py docstring)")
    return rows


def seed_catalog(db):
    products = []
    for row in load_catalog_rows():
        p = models.Product(
            sku=row["sku"], name=row["name"], category=row["category"],
            pack_size=row["pack_size"], unit_price=row["price"], active=True,
        )
        db.add(p)
        db.flush()
        qty = row["qty_on_hand"]
        threshold = random.choice([10, 15, 20, 25])
        db.add(models.Inventory(product_id=p.id, qty_on_hand=qty, reorder_threshold=threshold))
        db.add(models.InventoryTransaction(
            product_id=p.id, change_qty=qty,
            reason=models.InventoryReason.received_stock, reference="initial stock"
        ))
        products.append(p)
    db.commit()
    return products


def seed_customers_and_orders(db, products):
    customers = []
    for c in SAMPLE_CUSTOMERS:
        cust = models.Customer(**c)
        db.add(cust)
        customers.append(cust)
    db.commit()

    def add_order(customer, days_ago, target_status, carrier=None, packer=None):
        created = datetime.utcnow() - timedelta(days=days_ago)
        order = models.Order(
            order_number=f"AFB-{random.randint(100000,999999)}",
            customer_id=customer.id, status=models.OrderStatus.received,
            delivery_pref="Next available Tri-State delivery",
            created_at=created, updated_at=created,
        )
        db.add(order)
        db.flush()

        chosen = random.sample(products, k=min(len(products), random.randint(2, 5)))
        for p in chosen:
            qty = random.randint(1, 8)
            db.add(models.OrderItem(order_id=order.id, product_id=p.id, qty_ordered=qty,
                                     unit_price_snapshot=p.unit_price))
            inv = db.query(models.Inventory).filter(models.Inventory.product_id == p.id).first()
            inv.qty_reserved += qty
            db.add(models.InventoryTransaction(
                product_id=p.id, change_qty=-qty,
                reason=models.InventoryReason.order_reserved, reference=order.order_number,
            ))
        db.flush()

        stage_path = ["received", "confirmed", "packing", "packed", "out_for_delivery", "delivered"]
        target_idx = stage_path.index(target_status)
        t = created
        for i, stage in enumerate(stage_path[:target_idx + 1]):
            if i > 0:
                t = t + timedelta(hours=random.randint(2, 20))
            db.add(models.OrderStatusHistory(order_id=order.id, status=models.OrderStatus(stage), changed_at=t))
            order.status = models.OrderStatus(stage)

            if stage == "packed" and packer:
                for item in order.items:
                    item.qty_packed = item.qty_ordered
                db.add(models.PackingRecord(
                    order_id=order.id, packed_by=packer,
                    boxes=random.randint(1, 4), packed_at=t,
                ))
            if stage == "out_for_delivery" and carrier:
                shipment = models.Shipment(
                    order_id=order.id, carrier=carrier,
                    tracking_number=f"TRK{random.randint(100000,999999)}",
                    address=customer.address, status=models.ShipmentStatus.in_transit,
                    shipped_at=t,
                )
                db.add(shipment)
                db.flush()
                db.add(models.ShipmentEvent(shipment_id=shipment.id, status="in_transit",
                                             location="Paterson, NJ facility", created_at=t))
            if stage == "delivered" and carrier:
                shipment = db.query(models.Shipment).filter(models.Shipment.order_id == order.id).first()
                if shipment:
                    shipment.status = models.ShipmentStatus.delivered
                    shipment.delivered_at = t
                    db.add(models.ShipmentEvent(shipment_id=shipment.id, status="delivered",
                                                 location=customer.address, created_at=t))
        order.updated_at = t
        db.commit()
        return order

    o1 = add_order(customers[0], days_ago=6, target_status="delivered", carrier="AFB Fleet", packer="Luis M.")
    o2 = add_order(customers[1], days_ago=4, target_status="delivered", carrier="AFB Fleet", packer="Dana K.")
    o3 = add_order(customers[2], days_ago=3, target_status="out_for_delivery", carrier="Private Trucking Partner")
    o4 = add_order(customers[3], days_ago=2, target_status="packed", packer="Luis M.")
    add_order(customers[0], days_ago=1, target_status="confirmed")
    add_order(customers[2], days_ago=0, target_status="received")

    # sample pallets: one already shipped (the two delivered orders), one still being loaded
    pallet1 = models.Pallet(
        pallet_number=f"PLT-{random.randint(100000,999999)}", loaded_by="Luis M.",
        carrier="AFB Fleet", status=models.PalletStatus.shipped,
        shipped_at=o1.updated_at,
    )
    db.add(pallet1)
    db.flush()
    o1.pallet_id = pallet1.id
    o2.pallet_id = pallet1.id

    pallet2 = models.Pallet(
        pallet_number=f"PLT-{random.randint(100000,999999)}", loaded_by="Dana K.",
        carrier="Private Trucking Partner", status=models.PalletStatus.staged,
    )
    db.add(pallet2)
    db.flush()
    o3.pallet_id = pallet2.id
    o4.pallet_id = pallet2.id

    db.commit()

    return customers


def seed_packers_and_production(db, products):
    packers = []
    for name in SAMPLE_PACKERS:
        p = models.Packer(name=name, active=True)
        db.add(p)
        packers.append(p)
    db.commit()

    # a couple of sample assignments + logged production, so the demo isn't empty
    sample_products = random.sample(products, k=min(len(products), 4))

    a1 = models.PackingAssignment(
        product_id=sample_products[0].id, qty_assigned=200, assigned_to="Luis M.",
        assigned_by="Warehouse Manager", status=models.AssignmentStatus.in_progress,
        qty_completed=120,
    )
    a2 = models.PackingAssignment(
        product_id=sample_products[1].id, qty_assigned=150, assigned_to="Dana K.",
        assigned_by="Warehouse Manager", status=models.AssignmentStatus.assigned,
    )
    a3 = models.PackingAssignment(
        product_id=sample_products[2].id, qty_assigned=100, assigned_to="Marcus T.",
        assigned_by="Warehouse Manager", status=models.AssignmentStatus.completed,
        qty_completed=100,
    )
    db.add_all([a1, a2, a3])
    db.commit()

    db.add(models.PackerProductionLog(
        assignment_id=a1.id, product_id=sample_products[0].id, packer_name="Luis M.",
        qty_completed=120, notes="Morning run",
    ))
    db.add(models.PackerProductionLog(
        assignment_id=a3.id, product_id=sample_products[2].id, packer_name="Marcus T.",
        qty_completed=100, notes="Finished full assignment",
    ))
    db.commit()

    return packers


def seed_packaging_materials(db, products):
    """
    Indirect materials: containers, lids (separate items), shipping boxes, and
    general supplies (tape, hairnets, etc). These aren't sold to customers —
    they're internal stock the packing team consumes to package the real catalog.
    """
    containers = [
        ("PKG-CTR-8OZ", "8 oz Container", "Packaging - Containers"),
        ("PKG-CTR-12OZ", "12 oz Container", "Packaging - Containers"),
        ("PKG-CTR-16OZ", "16 oz Container", "Packaging - Containers"),
        ("PKG-CTR-24OZ", "24 oz Container", "Packaging - Containers"),
    ]
    lids = [
        ("PKG-LID-8OZ", "8 oz Lid", "Packaging - Lids"),
        ("PKG-LID-12OZ", "12 oz Lid", "Packaging - Lids"),
        ("PKG-LID-16OZ", "16 oz Lid", "Packaging - Lids"),
        ("PKG-LID-24OZ", "24 oz Lid", "Packaging - Lids"),
    ]
    boxes = [
        ("PKG-BOX-10x8x6", "Case Box 10x8x6", "Packaging - Boxes"),
        ("PKG-BOX-14x9x9", "Case Box 14x9x9", "Packaging - Boxes"),
        ("PKG-BOX-18x12x10", "Case Box 18x12x10", "Packaging - Boxes"),
    ]
    supplies = [
        ("PKG-TAPE-CLEAR", "Packing Tape (Clear)", "Packaging - Supplies"),
        ("PKG-TAPE-BRAND", "Packing Tape (Branded)", "Packaging - Supplies"),
        ("PPE-HAIRNET", "Hairnets", "PPE - Food Safety Supplies"),
        ("PPE-GLOVES-M", "Gloves (Medium)", "PPE - Food Safety Supplies"),
        ("PPE-GLOVES-L", "Gloves (Large)", "PPE - Food Safety Supplies"),
        ("PPE-APRON", "Aprons", "PPE - Food Safety Supplies"),
    ]

    created = {}
    for sku, name, category in containers + lids + boxes + supplies:
        p = models.Product(
            sku=sku, name=name, category=category,
            item_type=models.ProductType.indirect_material, active=True,
        )
        db.add(p)
        db.flush()
        qty = random.randint(200, 1500)
        db.add(models.Inventory(product_id=p.id, qty_on_hand=qty, reorder_threshold=100))
        db.add(models.InventoryTransaction(
            product_id=p.id, change_qty=qty,
            reason=models.InventoryReason.received_stock, reference="initial stock"
        ))
        created[sku] = p
    db.commit()

    # Sample packaging specs: link a handful of real sellable products to
    # containers/lids/boxes so the "materials needed" calculation has data
    # to demo. Picks products whose pack_size hints at a small retail unit.
    candidates = [p for p in products if p.pack_size and ("oz" in p.pack_size.lower())][:6]
    unit_size_map = {"8": "8OZ", "12": "12OZ", "16": "16OZ", "24": "24OZ"}

    specs_created = 0
    for p in candidates:
        # crude match: pick the first size token that appears in pack_size, default 12OZ
        size_key = next((v for k, v in unit_size_map.items() if k in p.pack_size), "12OZ")
        container = created.get(f"PKG-CTR-{size_key}")
        lid = created.get(f"PKG-LID-{size_key}")
        box = created.get("PKG-BOX-14x9x9")
        if not (container and lid and box):
            continue
        spec = models.PackagingSpec(
            product_id=p.id,
            container_product_id=container.id, container_qty_per_unit=1,
            lid_product_id=lid.id, lid_qty_per_unit=1,
            box_product_id=box.id, units_per_box=12,
            notes="Seeded sample spec — adjust units_per_box to match real case pack.",
        )
        db.add(spec)
        specs_created += 1
    db.commit()

    return len(created), specs_created


def run(catalog_only=False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if catalog_only:
        # wipe products/inventory only, leave customers/orders alone
        db.query(models.InventoryTransaction).delete()
        db.query(models.OrderItem).delete()  # order items reference products; drop first
        db.query(models.Inventory).delete()
        db.query(models.Product).delete()
        db.commit()
        products = seed_catalog(db)
        db.close()
        print(f"Reloaded catalog only: {len(products)} products. Existing customers/orders left untouched"
              " (note: any pre-existing orders referencing old products were cleared).")
        return

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    products = seed_catalog(db)
    customers = seed_customers_and_orders(db, products)
    packers = seed_packers_and_production(db, products)
    material_count, spec_count = seed_packaging_materials(db, products)
    db.close()
    print(f"Seeded {len(products)} products, {len(customers)} customers, 6 sample orders, "
          f"{len(packers)} packers with sample assignments, {material_count} packaging/PPE "
          f"materials, {spec_count} packaging specs.")


if __name__ == "__main__":
    run(catalog_only="--catalog-only" in sys.argv)
